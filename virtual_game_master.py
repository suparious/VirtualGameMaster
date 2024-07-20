import datetime
import json
import os
import re

from typing import Tuple, Generator
from typing import Callable, Dict
from functools import wraps

from dotenv import load_dotenv

from message_template import MessageTemplate
from chat_api import ChatAPI
from chat_history import ChatHistory, Message
from utilities import load_yaml_initial_game_state
from command_system import CommandSystem
import commands
# Load environment variables
load_dotenv()


class VirtualGameMasterConfig:
    GAME_SAVE_FOLDER = os.getenv('GAME_SAVE_FOLDER')
    INITIAL_GAME_STATE = os.getenv('INITIAL_GAME_STATE')
    MAX_MESSAGES = int(os.getenv('MAX_MESSAGES'))
    KEPT_MESSAGES = int(os.getenv('KEPT_MESSAGES'))
    SYSTEM_MESSAGE_FILE = os.getenv('SYSTEM_MESSAGE_FILE')
    SAVE_SYSTEM_MESSAGE_FILE = os.getenv('SAVE_SYSTEM_MESSAGE_FILE')
    SAVE_REMINDER_MESSAGE_FILE = os.getenv('SAVE_REMINDER_MESSAGE_FILE')
    API_KEY = os.getenv('API_KEY')
    MODEL = os.getenv('MODEL')


class VirtualGameMaster:
    def __init__(self, config: VirtualGameMasterConfig, api: ChatAPI, debug_mode: bool = False):
        self.config = config
        self.api = api
        self.system_message_template = MessageTemplate.from_file(
            config.SYSTEM_MESSAGE_FILE
        )
        self.save_system_message_template = MessageTemplate.from_file(
            config.SAVE_SYSTEM_MESSAGE_FILE
        )

        with open(config.SAVE_REMINDER_MESSAGE_FILE, "r") as file:
            self.reminder_message = file.read()

        self.template_fields = load_yaml_initial_game_state(config.INITIAL_GAME_STATE)
        self.history = ChatHistory(config.GAME_SAVE_FOLDER)
        self.history_offset = 0
        self.messages_since_last_save = 0
        self.debug_mode = debug_mode
        self.next_message_id = 0
        self.max_messages = config.MAX_MESSAGES
        self.kept_messages = config.KEPT_MESSAGES

    def process_input(self, user_input: str, stream: bool) -> Tuple[str, bool] | Tuple[
        Generator[str, None, None], bool]:

        if user_input.startswith("@"):
            command_parts = user_input[1:].split()
            command = command_parts[0]
            args = command_parts[1:]
            return CommandSystem.handle_command(self, command, *args)

        if stream:
            return self.get_streaming_response(user_input), False
        return self.get_response(user_input), False

    def get_response(self, user_input: str) -> str:
        history = self.pre_response(user_input)
        response = self.api.get_response(history)
        self.post_response(response)

        return response.strip()

    def get_streaming_response(self, user_input: str) -> Generator[str, None, None]:
        history = self.pre_response(user_input)
        full_response = ""
        for response_chunk in self.api.get_streaming_response(history):
            full_response += response_chunk
            yield response_chunk
        self.post_response(full_response)

    def pre_response(self, user_input: str) -> list[dict[str, str]]:
        self.history.add_message(Message("user", user_input.strip(), self.next_message_id))
        self.next_message_id += 1

        history = self.history.to_list()
        history = history[self.history_offset:]
        history.insert(0, {"role": "system",
                           "content": self.system_message_template.generate_message_content(
                               self.template_fields).strip()})

        if self.debug_mode:
            print(history[0]["content"])

        return history

    def post_response(self, response: str) -> None:
        self.history.add_message(Message("assistant", response.strip(), self.next_message_id))
        self.next_message_id += 1
        self.history.save_history()
        self.messages_since_last_save += 2

        if self.messages_since_last_save >= self.max_messages:
            self.generate_save_state()
            self.messages_since_last_save = 0

    def edit_message(self, message_id: int, new_content: str) -> bool:
        success = self.history.edit_message(message_id, new_content)
        if success:
            self.history.save_history()
        return success

    def manual_save(self):
        self.generate_save_state()
        self.messages_since_last_save = 0

    def generate_save_state(self):
        history = self.history.to_list()[self.history_offset:]
        history.insert(0, {"role": "system",
                           "content": self.save_system_message_template.generate_message_content(self.template_fields)})

        history.append({"role": "user", "content": self.reminder_message.strip()})

        response = self.api.get_response(history)

        if self.debug_mode:
            print(f"Update game info:\n{response}")

        self.update_template_fields(response)
        self.history_offset = len(self.history.messages) - self.kept_messages
        self.messages_since_last_save = 0
        self.save()

    def update_template_fields(self, save_state: str):
        sections = re.findall(r'<(\w+)>(.*?)</\1>', save_state, re.DOTALL)
        for section, content in sections:
            self.template_fields[section] = content.strip()

    def save(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_id = f"{timestamp}"
        filename = f"save_state_{save_id}.json"
        save_data = {
            "template_fields": self.template_fields,
            "history_offset": self.history_offset,
            "messages_since_last_save": self.messages_since_last_save,
            "next_message_id": self.next_message_id
        }
        with open(f"{self.config.GAME_SAVE_FOLDER}/{filename}", "w") as f:
            json.dump(save_data, f)

    def load(self):
        self.history.load_history()
        self.next_message_id = max([msg.id for msg in self.history.messages], default=-1) + 1

        save_files = [f for f in os.listdir(self.config.GAME_SAVE_FOLDER) if
                      f.startswith("save_state_") and f.endswith(".json")]

        if not save_files:
            print("No save state found. Starting a new game.")
            return

        # Sort save files based on the timestamp in the filename
        latest_save = sorted(save_files, reverse=True)[0]

        try:
            with open(f"{self.config.GAME_SAVE_FOLDER}/{latest_save}", "r") as f:
                save_data = json.load(f)
            self.template_fields = save_data.get("template_fields", self.template_fields)
            self.history_offset = save_data.get("history_offset", 0)
            self.messages_since_last_save = save_data.get("messages_since_last_save", 0)
            self.next_message_id = save_data.get("next_message_id", self.next_message_id)
            print(f"Loaded the most recent game state: {latest_save}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading save state: {e}. Starting a new game.")
