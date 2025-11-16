"""
OLED Menu System
Provides interactive menu navigation
"""

import logging
from typing import Optional, Callable, List, Dict, Any
from ui.display import Display

logger = logging.getLogger(__name__)


class MenuItem:
    """Single menu item"""

    def __init__(self, label: str, action: Optional[Callable] = None, submenu: Optional['Menu'] = None):
        """
        Initialize menu item

        Args:
            label: Display label
            action: Callback function to execute
            submenu: Submenu to navigate to
        """
        self.label = label
        self.action = action
        self.submenu = submenu

    def execute(self) -> Optional['Menu']:
        """
        Execute menu item

        Returns:
            Submenu if available, None otherwise
        """
        if self.action:
            try:
                self.action()
            except Exception as e:
                logger.error(f"Error executing menu action: {e}")

        return self.submenu


class Menu:
    """Menu with multiple items"""

    def __init__(self, title: str, parent: Optional['Menu'] = None):
        """
        Initialize menu

        Args:
            title: Menu title
            parent: Parent menu (for back navigation)
        """
        self.title = title
        self.parent = parent
        self.items: List[MenuItem] = []
        self.selected_index = 0

    def add_item(self, label: str, action: Optional[Callable] = None, submenu: Optional['Menu'] = None):
        """
        Add menu item

        Args:
            label: Item label
            action: Optional callback
            submenu: Optional submenu
        """
        item = MenuItem(label, action, submenu)
        self.items.append(item)

    def add_back_item(self):
        """Add a 'Back' item that returns to parent menu"""
        if self.parent:
            self.add_item("< Back", submenu=self.parent)

    def next_item(self):
        """Select next menu item"""
        if self.items:
            self.selected_index = (self.selected_index + 1) % len(self.items)

    def previous_item(self):
        """Select previous menu item"""
        if self.items:
            self.selected_index = (self.selected_index - 1) % len(self.items)

    def select(self) -> Optional['Menu']:
        """
        Select current item

        Returns:
            Next menu to navigate to (or None to stay)
        """
        if self.items and 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index].execute()
        return None

    def get_item_labels(self) -> List[str]:
        """Get all item labels"""
        return [item.label for item in self.items]


class MenuSystem:
    """Complete menu system with display integration"""

    def __init__(self, display: Display, controller):
        """
        Initialize menu system

        Args:
            display: Display instance
            controller: DMX controller instance
        """
        self.display = display
        self.controller = controller
        self.current_menu: Optional[Menu] = None
        self.root_menu: Optional[Menu] = None

        self.build_menus()

    def build_menus(self):
        """Build the menu structure"""
        # Root menu
        self.root_menu = Menu("Main Menu")
        self.root_menu.add_item("Fixtures", submenu=self._build_fixture_menu())
        self.root_menu.add_item("Scenes", submenu=self._build_scene_menu())
        self.root_menu.add_item("Settings", submenu=self._build_settings_menu())
        self.root_menu.add_item("Status", action=self._show_status)

        self.current_menu = self.root_menu

    def _build_fixture_menu(self) -> Menu:
        """Build fixtures submenu"""
        menu = Menu("Fixtures", parent=self.root_menu)

        # Dynamically populate fixtures
        fixtures = self.controller.fixture_manager.get_all_fixtures()
        for fixture in fixtures:
            menu.add_item(
                fixture.name,
                action=lambda f=fixture: self.controller.select_fixture(f.id)
            )

        if not fixtures:
            menu.add_item("(No fixtures)")

        menu.add_back_item()
        return menu

    def _build_scene_menu(self) -> Menu:
        """Build scenes submenu"""
        menu = Menu("Scenes", parent=self.root_menu)

        # Scene actions
        recall_menu = Menu("Recall Scene", parent=menu)
        scenes = self.controller.scene_manager.get_all_scenes()

        for scene in scenes:
            recall_menu.add_item(
                scene.name,
                action=lambda s=scene: self.controller.recall_scene(s.id)
            )

        if not scenes:
            recall_menu.add_item("(No scenes)")

        recall_menu.add_back_item()

        menu.add_item("Recall", submenu=recall_menu)
        menu.add_item("Capture Current", action=self._capture_scene_wizard)
        menu.add_item("Blackout", action=self.controller.blackout)
        menu.add_back_item()

        return menu

    def _build_settings_menu(self) -> Menu:
        """Build settings submenu"""
        menu = Menu("Settings", parent=self.root_menu)

        menu.add_item("Save Config", action=self._save_config)
        menu.add_item("Load Config", action=self._load_config)
        menu.add_item("Backup", action=self._backup_config)

        mode_menu = Menu("Control Mode", parent=menu)
        mode_menu.add_item("Direct", action=lambda: self.controller.set_mode("direct"))
        mode_menu.add_item("Fixture", action=lambda: self.controller.set_mode("fixture"))
        mode_menu.add_item("Scene", action=lambda: self.controller.set_mode("scene"))
        mode_menu.add_back_item()

        menu.add_item("Mode", submenu=mode_menu)
        menu.add_back_item()

        return menu

    def _show_status(self):
        """Show controller status"""
        status = self.controller.get_status()
        self.display.draw_status(status)

    def _save_config(self):
        """Save configuration"""
        self.controller.save_configuration()
        self.display.show_message("Config Saved", 1.5)

    def _load_config(self):
        """Load configuration"""
        self.controller.load_configuration()
        self.display.show_message("Config Loaded", 1.5)

    def _backup_config(self):
        """Create configuration backup"""
        backup_path = self.controller.storage.backup()
        if backup_path:
            self.display.show_message("Backup Created", 1.5)
        else:
            self.display.show_message("Backup Failed", 1.5)

    def _capture_scene_wizard(self):
        """Wizard for capturing a scene (simplified)"""
        import time
        scene_id = f"scene_{int(time.time())}"
        scene_name = f"Scene {len(self.controller.scene_manager.scenes) + 1}"

        if self.controller.capture_scene(scene_id, scene_name):
            self.display.show_message(f"Captured:\n{scene_name}", 1.5)
        else:
            self.display.show_message("Capture Failed", 1.5)

    def navigate_up(self):
        """Navigate up in menu"""
        if self.current_menu:
            self.current_menu.previous_item()
            self.render()

    def navigate_down(self):
        """Navigate down in menu"""
        if self.current_menu:
            self.current_menu.next_item()
            self.render()

    def select_item(self):
        """Select current menu item"""
        if self.current_menu:
            next_menu = self.current_menu.select()
            if next_menu:
                self.current_menu = next_menu
            self.render()

    def go_back(self):
        """Go back to parent menu"""
        if self.current_menu and self.current_menu.parent:
            self.current_menu = self.current_menu.parent
            self.render()

    def go_to_root(self):
        """Go to root menu"""
        self.current_menu = self.root_menu
        self.render()

    def render(self):
        """Render current menu to display"""
        if self.current_menu:
            items = self.current_menu.get_item_labels()
            self.display.draw_menu(
                self.current_menu.title,
                items,
                self.current_menu.selected_index
            )

    def refresh_fixtures(self):
        """Refresh fixtures menu (call after adding/removing fixtures)"""
        # Rebuild fixture submenu
        for i, item in enumerate(self.root_menu.items):
            if item.label == "Fixtures":
                self.root_menu.items[i].submenu = self._build_fixture_menu()
                break
