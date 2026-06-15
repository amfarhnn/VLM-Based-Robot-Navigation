from __future__ import annotations

import unittest

import cv2
import numpy as np

from laptop_navigation_demo import parse_instruction, process_navigation_frame


class DoorDetectionTests(unittest.TestCase):
    def make_scene(self, door_box: tuple[int, int, int, int] | None) -> np.ndarray:
        frame = np.full((480, 640, 3), (225, 225, 225), dtype=np.uint8)
        frame[365:, :] = (205, 205, 205)
        cv2.line(frame, (0, 400), (640, 400), (170, 145, 125), 8)
        cv2.rectangle(frame, (440, 130), (580, 280), (60, 135, 190), -1)
        if door_box:
            x, y, width, height = door_box
            cv2.rectangle(frame, (x, y), (x + width, y + height), (105, 115, 105), -1)
            cv2.rectangle(frame, (x, y), (x + width, y + height), (75, 95, 90), 5)
        return frame

    def action_for(self, door_box: tuple[int, int, int, int] | None) -> str:
        goal = parse_instruction("find the door")
        action, _box, _mask = process_navigation_frame(self.make_scene(door_box), goal)
        return action

    def test_door_actions(self) -> None:
        self.assertTrue(self.action_for(None).startswith("SEARCH"))
        self.assertTrue(self.action_for((35, 45, 145, 310)).startswith("TURN LEFT"))
        self.assertTrue(self.action_for((245, 35, 150, 325)).startswith("MOVE FORWARD"))
        self.assertTrue(self.action_for((465, 45, 145, 310)).startswith("TURN RIGHT"))
        self.assertTrue(self.action_for((115, 10, 410, 445)).startswith("STOP"))


if __name__ == "__main__":
    unittest.main()
