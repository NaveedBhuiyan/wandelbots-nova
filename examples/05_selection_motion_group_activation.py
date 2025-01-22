import asyncio
from math import pi

from nova.api import models
from nova import MotionGroup, Nova
from nova.actions import ptp
from nova.types import Pose

"""
Example: Move multiple robots to perform coordinated movements.

Prerequisites:
- A cell with two robots named "ur" and "kuka".
"""


async def move_robot(motion_group: MotionGroup, tcp: str):
    home_pose = Pose((200, 200, 600, 0, pi, 0))
    target_pose = home_pose @ (100, 0, 0, 0, 0, 0)
    actions = [
        ptp(home_pose),
        ptp(target_pose),
        ptp(target_pose @ (0, 0, 100, 0, 0, 0)),
        ptp(target_pose @ (0, 100, 0, 0, 0, 0)),
        ptp(home_pose),
    ]

    await motion_group.plan_and_execute(actions, tcp=tcp)


async def main():
    async with Nova() as nova:
        cell = nova.cell()
        ur10 = await cell.ensure_virtual_robot_controller(
            "ur10",
            models.VirtualControllerTypes.UNIVERSALROBOTS_MINUS_UR10E,
            models.Manufacturer.UNIVERSALROBOTS,
        )
        ur5 = await cell.ensure_virtual_robot_controller(
            "ur5",
            models.VirtualControllerTypes.UNIVERSALROBOTS_MINUS_UR5E,
            models.Manufacturer.UNIVERSALROBOTS,
        )
        tcp = "Flange"

        flange_state = await ur10[0].get_state(tcp)
        print(flange_state)

        # activate all motion groups
        async with ur10:
            await move_robot(ur10.motion_group(0), tcp)

        # activate motion group 0
        async with ur10.motion_group(0) as mg_0:
            await move_robot(mg_0, tcp)

        # activate motion group 0
        async with ur10[0] as mg_0:
            await move_robot(mg_0, tcp)

        # activate motion group 0 from two different controllers
        async with ur10[0] as ur_0_mg, ur5[0] as kuka_0_mg:
            await asyncio.gather(move_robot(ur_0_mg, tcp), move_robot(kuka_0_mg, tcp))

        # activate motion group 0 from two different controllers
        mg_0 = ur10.motion_group(0)
        mg_1 = ur5.motion_group(0)
        async with mg_0, mg_1:
            await asyncio.gather(move_robot(mg_0, tcp), move_robot(mg_1, tcp))

        await cell.delete_robot_controller(ur5.name)
        await cell.delete_robot_controller(ur10.name)


if __name__ == "__main__":
    asyncio.run(main())
