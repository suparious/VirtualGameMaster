import json
from typing import List, Dict, Any, Optional
from enum import Enum, auto

import graphviz
import networkx as nx
from pydantic import BaseModel, Field


class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_entity(self, entity: str, attributes: Dict[str, Any]) -> None:
        """Add an entity (node) to the graph with attributes."""
        self.graph.add_node(entity, **attributes)

    def add_relationship(self, entity1: str, entity2: str, relationship: str,
                         attributes: Dict[str, Any] = None) -> None:
        """Add a directional relationship (edge) between two entities with optional attributes."""
        self.graph.add_edge(entity1, entity2, relationship=relationship, **attributes or {})

    def get_entity_attributes(self, entity: str) -> Dict[str, Any]:
        """Get all attributes of a given entity."""
        return dict(self.graph.nodes[entity])

    def update_entity_attributes(self, entity: str, attributes: Dict[str, Any]) -> None:
        """Update attributes for a given entity."""
        self.graph.nodes[entity].update(attributes)

    def get_relationships(self, entity: str) -> List[Dict[str, Any]]:
        """Get all relationships for a given entity."""
        relationships = []
        for _, neighbor, data in self.graph.edges(entity, data=True):
            relationships.append({
                "target": neighbor,
                "type": data["relationship"],
                "attributes": {k: v for k, v in data.items() if k != "relationship"}
            })
        return relationships

    def query_entities(self, attribute_filter: Dict[str, Any]) -> List[str]:
        """Query entities based on attribute filters."""
        return [node for node, data in self.graph.nodes(data=True)
                if all(data.get(k) == v for k, v in attribute_filter.items())]

    def query_relationships(self, start_entity: str, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query relationships of a specific type from a starting entity."""
        relationships = []
        for _, target, data in self.graph.edges(start_entity, data=True):
            if relationship_type is None or data["relationship"] == relationship_type:
                relationships.append({
                    "target": target,
                    "type": data["relationship"],
                    "attributes": {k: v for k, v in data.items() if k != "relationship"}
                })
        return relationships

    def find_path(self, start_entity: str, end_entity: str, relationship_types: Optional[List[str]] = None) -> List[
        str]:
        """Find a path between two entities, optionally constrained by relationship types."""
        if relationship_types:
            def edge_filter(u, v, d):
                return d["relationship"] in relationship_types

            path = nx.shortest_path(self.graph, start_entity, end_entity, weight=None, method="dijkstra",
                                    edge_filter=edge_filter)
        else:
            path = nx.shortest_path(self.graph, start_entity, end_entity)
        return path

    def get_subgraph(self, center_entity: str, max_depth: int = 2) -> Dict[str, Any]:
        """Get a subgraph centered on an entity up to a certain depth."""
        subgraph = nx.ego_graph(self.graph, center_entity, radius=max_depth)
        return nx.node_link_data(subgraph)

    def visualize(self, output_file: str = "knowledge_graph", format: str = "png") -> None:
        """
        Visualize the knowledge graph using Graphviz.
        Args:
            output_file: Name of the output file (without extension)
            format: Output format (e.g., "png", "pdf", "svg")
        """
        dot = graphviz.Digraph(comment="Knowledge Graph")
        dot.attr(rankdir="LR", size="8,5")

        # Add nodes
        for node, data in self.graph.nodes(data=True):
            label = f"{node}\n{json.dumps(data, indent=2)}"
            dot.node(node, label)

        # Add edges
        for u, v, data in self.graph.edges(data=True):
            label = data.get("relationship", "")
            dot.edge(u, v, label=label)

        # Render the graph
        dot.render(output_file, format=format, cleanup=True)
        print(f"Graph visualization saved as {output_file}.{format}")

    def save_to_json(self, filename: str) -> None:
        """Save the graph to a JSON file."""
        data = nx.node_link_data(self.graph)
        with open(filename, 'w') as f:
            json.dump(data, f)

    @classmethod
    def load_from_json(cls, filename: str) -> 'KnowledgeGraph':
        """Load the graph from a JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        kg = cls()
        kg.graph = nx.node_link_graph(data, multigraph=True, directed=True)
        return kg


class EntityType(str, Enum):
    CHARACTER = "Character"
    BEAST = "Beast"
    LOCATION = "Location"
    ITEM = "Item"
    QUEST = "Quest"
    EVENT = "Event"
    FACTION = "Faction"


class CharacterType(str, Enum):
    NPC = "Non-Player-Character"
    PLAYER = "Player-Character"
    DEITY = "Deity"
    HISTORICAL_FIGURE = "Historical-Figure"


class BeastType(str, Enum):
    ANIMAL = "Animal"
    MONSTER = "Monster"
    NON_MONSTER = "Non-Monster"
    MYTHICAL = "Mythical"
    UNDEAD = "Undead"
    CONSTRUCT = "Construct"
    ELEMENTAL = "Elemental"


class LocationType(str, Enum):
    PLANE = "Plane"
    CITY = "City"
    CITY_DISTRICT = "City-District"
    TOWN = "Town"
    VILLAGE = "Village"
    DUNGEON = "Dungeon"
    WILDERNESS = "Wilderness"
    TEMPLE = "Temple"
    CASTLE = "Castle"
    TAVERN = "Tavern"
    INN = "Inn"
    SHOP = "Shop"
    HOUSE = "House"


class ItemType(str, Enum):
    WEAPON = "Weapon"
    ARMOR = "Armor"
    POTION = "Potion"
    EQUIPMENT = "Equipment"
    SCROLL = "Scroll"
    WAND = "Wand"
    RING = "Ring"
    ARTIFACT = "Artifact"
    MISC = "Miscellaneous"


class QuestType(str, Enum):
    FIND_CHARACTER = "Find Character"
    FIND_ITEM = "Find Item"
    KILL_MONSTER = "Kill Monster"
    KILL_CHARACTER = "Kill Character"
    ESCORT = "Escort"
    EXPLORE = "Explore"
    RESCUE = "Rescue"
    DELIVER = "Deliver"


class EventType(str, Enum):
    HISTORY = "History"
    LORE = "Lore"
    FESTIVAL = "Festival"
    MURDER = "Murder"
    BATTLE = "Battle"
    NATURAL_DISASTER = "Natural Disaster"
    RITUAL = "Ritual"


class FactionType(str, Enum):
    CORPORATION = "Corporation"
    GUILD = "Guild"
    GROUP = "Group"
    GOVERNMENT = "Government"
    CULT = "Cult"
    TRIBE = "Tribe"


class RelationshipType(str, Enum):
    # Character relationships
    ALLY = "Ally"
    ENEMY = "Enemy"
    FRIEND = "Friend"
    FAMILY = "Family"
    MENTOR = "Mentor"
    STUDENT = "Student"
    RIVAL = "Rival"
    LOVER = "Lover"
    SPOUSE = "Spouse"

    # Location relationships
    RESIDES_IN = "Resides In"
    RULES = "Rules"
    OWNS = "Owns"
    GUARDS = "Guards"
    LOCATED_IN = "Located In"

    # Item relationships
    POSSESSES = "Possesses"
    CREATED = "Created"
    SEEKS = "Seeks"

    # Quest relationships
    ASSIGNED_BY = "Assigned By"
    INVOLVES = "Involves"
    REWARDS = "Rewards"

    # Event relationships
    PARTICIPATED_IN = "Participated In"
    CAUSED = "Caused"
    AFFECTED_BY = "Affected By"

    # Faction relationships
    MEMBER_OF = "Member Of"
    ALLIED_WITH = "Allied With"
    AT_WAR_WITH = "At War With"
    TRADING_PARTNER = "Trading Partner"

    # Beast relationships
    TAMED_BY = "Tamed By"
    HUNTS = "Hunts"
    INHABITS = "Inhabits"

    # General relationships
    KNOWS_ABOUT = "Knows About"
    INTERACTS_WITH = "Interacts With"
    PROTECTS = "Protects"
    THREATENS = "Threatens"
    WORSHIPS = "Worships"


class GameEntity(BaseModel):
    entity_type: EntityType


class Character(GameEntity):
    """
    Represents a Character.
    """
    entity_type = EntityType.CHARACTER
    character_name: str = Field(..., description="The name of the character.")
    character_type: CharacterType = Field(..., description="The type of character.")
    age: int = Field(..., description="The age of the character.")
    race: str = Field(..., description="The race of the character.")
    gender: str = Field(..., description="The gender of the character.")
    description: str = Field(..., description="The description of the character.")


class Beast(GameEntity):
    """
    Represents a Beast.
    """
    entity_type = EntityType.BEAST
    beast_name = str = Field(..., description="The name of the beast.")
    beast_type = BeastType = Field(..., description="The type of the beast.")
    age: int = Field(..., description="The age of the beast.")
    race: str = Field(..., description="The race of the beast.")
    gender: str = Field(..., description="The gender of the beast.")
    description: str = Field(..., description="The description of the beast.")


class Location(GameEntity):
    """
    Represents a Location.
    """
    entity_type = EntityType.LOCATION
    location_name: str = Field(..., description="The name of the location.")
    location_type = LocationType = Field(..., description="The type of the location.")
    description: str = Field(..., description="The description of the location.")


class Item(GameEntity):
    """
    Represents an Item.
    """
    entity_type = EntityType.ITEM
    item_name: str = Field(..., description="The name of the item.")
    item_type: ItemType = Field(..., description="The type of item.")
    description: str = Field(..., description="The description of the item.")


class Quest(GameEntity):
    """
    Represents a Quest.
    """
    entity_type = EntityType.QUEST
    quest_name: str = Field(..., description="The name of the quest.")
    quest_type: QuestType = Field(..., description="The type of quest.")
    description: str = Field(..., description="The description of the quest.")


class Event(GameEntity):
    """
    Represents an Event.
    """
    entity_type = EntityType.EVENT
    event_name: str = Field(..., description="The name of the event.")
    event_type: EventType = Field(..., description="The type of event.")
    description: str = Field(..., description="The description of the event.")


class Faction(GameEntity):
    """
    Represents a Faction.
    """
    entity_type = EntityType.FACTION
    faction_name: str = Field(..., description="The name of the faction.")
    faction_type: FactionType = Field(..., description="The type of faction.")
    description: str = Field(..., description="The description of the faction.")


class Relationship(BaseModel):
    """
    Represents a Relationship.
    """
    first_entity_id: str = Field(..., description="The entity id of the first entity.")
    relationship_type: RelationshipType = Field(..., description="The type of relationship.")
    second_entity_id: str = Field(..., description="The entity id of the second entity.")
    description: str = Field(..., description="The description of the relationship.")


class GameWorldKnowledgeGraph:
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        self.entity_counters = {
            EntityType.CHARACTER: 0,
            EntityType.BEAST: 0,
            EntityType.LOCATION: 0,
            EntityType.ITEM: 0,
            EntityType.QUEST: 0,
            EntityType.EVENT: 0,
            EntityType.FACTION: 0
        }

    def generate_entity_id(self, entity_type: EntityType) -> str:
        self.entity_counters[entity_type] += 1
        return f"{entity_type.name}-{self.entity_counters[entity_type]}"

    def add_character(self, character: Character):
        """
        Adds a character to the game world knowledge graph. Returns the entity id of the character added.
        Args:
            character(Character): The character to add.
        """
        entity_id = self.generate_entity_id(EntityType.CHARACTER)
        self.knowledge_graph.add_entity(entity_id, character.model_dump(mode="json"))
        return "Character entity added to game world knowledge graph with entity id: " + entity_id

    def add_beast(self, beast: Beast):
        """
        Adds a beast to the game world knowledge graph. Returns the entity id of the beast added.
        Args:
            beast(Beast): The beast to add.
        """
        entity_id = self.generate_entity_id(EntityType.BEAST)
        self.knowledge_graph.add_entity(entity_id, beast.model_dump(mode="json"))
        return "Beast entity added to game world knowledge graph with entity id: " + entity_id

    def add_location(self, location: Location):
        """
        Adds a location to the game world knowledge graph. Returns the entity id of the location added.
        Args:
            location(Location): The location to add.
        """
        entity_id = self.generate_entity_id(EntityType.LOCATION)
        self.knowledge_graph.add_entity(entity_id, location.model_dump(mode="json"))
        return "Location entity added to game world knowledge graph with entity id: " + entity_id

    def add_item(self, item: Item):
        """
        Adds an item to the game world knowledge graph. Returns the entity id of the item added.
        Args:
            item(Item): The item to add.
        """
        entity_id = self.generate_entity_id(EntityType.ITEM)
        self.knowledge_graph.add_entity(entity_id, item.model_dump(mode="json"))
        return "Item entity added to game world knowledge graph with entity id: " + entity_id

    def add_quest(self, quest: Quest):
        """
        Adds a quest to the game world knowledge graph. Returns the entity id of the quest added.
        Args:
            quest(Quest): The quest to add.
        """
        entity_id = self.generate_entity_id(EntityType.QUEST)
        self.knowledge_graph.add_entity(entity_id, quest.model_dump(mode="json"))
        return "Quest entity added to game world knowledge graph with entity id: " + entity_id

    def add_event(self, event: Event):
        """
        Adds an event to the game world knowledge graph. Returns the entity id of the event added.
        Args:
            event(Event): The event to add.
        """
        entity_id = self.generate_entity_id(EntityType.EVENT)
        self.knowledge_graph.add_entity(entity_id, event.model_dump(mode="json"))
        return "Event entity added to game world knowledge graph with entity id: " + entity_id

    def add_faction(self, faction: Faction):
        """
        Adds a faction to the game world knowledge graph. Returns the entity id of the faction added.
        Args:
            faction(Faction): The faction to add.
        """
        entity_id = self.generate_entity_id(EntityType.FACTION)
        self.knowledge_graph.add_entity(entity_id, faction.model_dump(mode="json"))
        return "Faction entity added to game world knowledge graph with entity id: " + entity_id

    def add_relationship(self, relationship: Relationship):
        """
        Adds a relationship between two entities to the game world knowledge graph.
        Args:
            relationship(Relationship): The relationship to add.
        """
        self.knowledge_graph.add_relationship(relationship.first_entity_id, relationship.second_entity_id,
                                              relationship.relationship_type.name,
                                              {"description": relationship.description})
        return "Relationship successful added to game world knowledge graph."

    def query_characters(self, character_type: Optional[CharacterType] = None, name: Optional[str] = None,
                         age: Optional[int] = None, race: Optional[str] = None,
                         gender: Optional[str] = None, location: Optional[str] = None):
        """
        Queries the characters stored in the game world knowledge graph.
        Args:
            character_type(Optional[CharacterType]): The type of character to query.
            name(Optional[str]): The name of the character to query. Allows partial matches.
            age(Optional[int]): The age of the character to query.
            race(Optional[str]): The race of the character to query. Allows partial matches.
            gender(Optional[str]): The gender of the character to query. Allows partial matches.
            location(Optional[str]): The location of the character to query. Allows partial matches.
        """
        def filter_func(node, data):
            if data['entity_type'] != EntityType.CHARACTER:
                return False
            if character_type and data['character_type'] != character_type:
                return False
            if name and name.lower() not in data['character_name'].lower():
                return False
            if age is not None and data['age'] != age:
                return False
            if race and race.lower() not in data['race'].lower():
                return False
            if gender and gender.lower() not in data['gender'].lower():
                return False
            if location:
                # Check if character is related to the given location
                for _, target, edge_data in self.knowledge_graph.graph.edges(node, data=True):
                    if (edge_data['relationship'] == RelationshipType.RESIDES_IN.name and
                            location.lower() in self.knowledge_graph.graph.nodes[target]['location_name'].lower()):
                        return True
                return False
            return True

        return [node for node, data in self.knowledge_graph.graph.nodes(data=True) if filter_func(node, data)]

    def query_beast(self, beast_type: Optional[BeastType] = None, name: Optional[str] = None, age: Optional[int] = None,
                    race: Optional[str] = None,
                    gender: Optional[str] = None, location: Optional[str] = None):
        """
        Queries the beasts stored in the game world knowledge graph.
        Args:
            beast_type(Optional[BeastType]): The type of beast to query.
            name(Optional[str]): The name of the beast to query. Allows partial matches.
            age(Optional[int]): The age of the beast to query.
            race(Optional[str]): The race of the beast to query. Allows partial matches.
            gender(Optional[str]): The gender of the beast to query. Allows partial matches.
            location(Optional[str]): The location of the beast to query. Allows partial matches.
        """
        def filter_func(node, data):
            if data['entity_type'] != EntityType.BEAST:
                return False
            if beast_type and data['beast_type'] != beast_type:
                return False
            if name and name.lower() not in data['beast_name'].lower():
                return False
            if age is not None and data['age'] != age:
                return False
            if race and race.lower() not in data['race'].lower():
                return False
            if gender and gender.lower() not in data['gender'].lower():
                return False
            if location:
                # Check if beast is related to the given location
                for _, target, edge_data in self.knowledge_graph.graph.edges(node, data=True):
                    if (edge_data['relationship'] == RelationshipType.INHABITS.name and
                            location.lower() in self.knowledge_graph.graph.nodes[target]['location_name'].lower()):
                        return True
                return False
            return True

        return [node for node, data in self.knowledge_graph.graph.nodes(data=True) if filter_func(node, data)]


    def query_location(self, location_type: Optional[LocationType] = None, name: Optional[str] = None):
        """
        Queries the locations stored in the game world knowledge graph.
        Args:
            location_type(Optional[LocationType]): The type of location to query.
            name(Optional[str]): The name of the location to query. Allows partial matches.
        """
        def filter_func(node, data):
            if data['entity_type'] != EntityType.LOCATION:
                return False
            if location_type and data['location_type'] != location_type:
                return False
            if name and name.lower() not in data['location_name'].lower():
                return False
            return True

        return [node for node, data in self.knowledge_graph.graph.nodes(data=True) if filter_func(node, data)]

    def query_items(self, item_type: Optional[ItemType] = None, name: Optional[str] = None):
        """
        Queries the items stored in the game world knowledge graph.
        Args:
            item_type(Optional[ItemType]): The type of item to query.
            name(Optional[str]): The name of the item to query. Allows partial matches.
        """

        def filter_func(node, data):
            if data['entity_type'] != EntityType.ITEM:
                return False
            if item_type and data['item_type'] != item_type:
                return False
            if name and name.lower() not in data['item_name'].lower():
                return False
            return True

        return [node for node, data in self.knowledge_graph.graph.nodes(data=True) if filter_func(node, data)]

    def query_quests(self, quest_type: Optional[QuestType] = None, name: Optional[str] = None):
        """
        Queries the quests stored in the game world knowledge graph.
        Args:
            quest_type(Optional[QuestType]): The type of quest to query.
            name(Optional[str]): The name of the quest to query. Allows partial matches.
        """

        def filter_func(node, data):
            if data['entity_type'] != EntityType.QUEST:
                return False
            if quest_type and data['quest_type'] != quest_type:
                return False
            if name and name.lower() not in data['quest_name'].lower():
                return False
            return True

        return [node for node, data in self.knowledge_graph.graph.nodes(data=True) if filter_func(node, data)]

    def query_events(self, event_type: Optional[EventType] = None, name: Optional[str] = None):
        """
        Queries the events stored in the game world knowledge graph.
        Args:
            event_type(Optional[EventType]): The type of event to query.
            name(Optional[str]): The name of the event to query. Allows partial matches.
        """

        def filter_func(node, data):
            if data['entity_type'] != EntityType.EVENT:
                return False
            if event_type and data['event_type'] != event_type:
                return False
            if name and name.lower() not in data['event_name'].lower():
                return False
            return True

        return [node for node, data in self.knowledge_graph.graph.nodes(data=True) if filter_func(node, data)]

    def query_factions(self, faction_type: Optional[FactionType] = None, name: Optional[str] = None):
        """
        Queries the factions stored in the game world knowledge graph.
        Args:
            faction_type(Optional[FactionType]): The type of faction to query.
            name(Optional[str]): The name of the faction to query. Allows partial matches.
        """

        def filter_func(node, data):
            if data['entity_type'] != EntityType.FACTION:
                return False
            if faction_type and data['faction_type'] != faction_type:
                return False
            if name and name.lower() not in data['faction_name'].lower():
                return False
            return True

        return [node for node, data in self.knowledge_graph.graph.nodes(data=True) if filter_func(node, data)]

    def save(self, filename: str) -> None:
        """
        Save the GameWorldKnowledgeGraph to a JSON file.

        Args:
            filename (str): The name of the file to save to.
        """

        data = {
            "knowledge_graph": self.knowledge_graph.graph,
            "entity_counters": {k.name: v for k, v in self.entity_counters.items()}
        }

        with open(filename, 'w') as f:
            json.dump(nx.node_link_data(data["knowledge_graph"]), f)
            json.dump(data["entity_counters"], f)

        print(f"GameWorldKnowledgeGraph saved to {filename}")

    @classmethod
    def load(cls, filename: str) -> 'GameWorldKnowledgeGraph':
        """
        Load a GameWorldKnowledgeGraph from a JSON file.

        Args:
            filename (str): The name of the file to load from.

        Returns:
            GameWorldKnowledgeGraph: The loaded GameWorldKnowledgeGraph instance.
        """
        with open(filename, 'r') as f:
            graph_data = json.load(f)
            counter_data = json.load(f)

        game_world = cls()
        game_world.knowledge_graph.graph = nx.node_link_graph(graph_data, multigraph=True, directed=True)
        game_world.entity_counters = {EntityType[k]: v for k, v in counter_data.items()}

        print(f"GameWorldKnowledgeGraph loaded from {filename}")
        return game_world
