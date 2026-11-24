"""Fit gesture targets to wrist, elbow, and palm landmarks on the corrected rig."""
from kinematics27 import *
import json

candidate = Asset(root / 'outputs/zachary_character_v27_candidate.glb')
node_data = candidate.g['nodes']
source = Path(r'D:\omni-workstation\projects\ZacharyPortfolio\src\graphics\SceneController.ts').read_text(encoding='utf-8')
station_candidates = [{key: float(value) for key, value in re.findall(r'(\w+)\s*:\s*(-?\d+(?:\.\d+)?)', block)}
                      for block in re.findall(r'gltf:\s*\{([^}]+)\}', source)]
station = next(values for values in station_candidates if 'rightArmX' in values)
rest_pose = world(node_data=node_data)

def arm_fit(side, wrist, direction, spread, elbow_bias):
    bone_names = [side + suffix for suffix in ['Arm', 'ForeArm', 'Hand']]
    prefixes = [side.lower() + suffix for suffix in ['Arm', 'Fore', 'Hand']]
    initial = np.array([station[prefix + axis] for prefix in prefixes for axis in 'XYZ'])
    shoulder = rest_pose[side + 'Arm'][:3, 3]
    old_elbow = rest_pose[side + 'ForeArm'][:3, 3]
    old_wrist = rest_pose[side + 'Hand'][:3, 3]
    upper_length = np.linalg.norm(old_elbow - shoulder)
    lower_length = np.linalg.norm(old_wrist - old_elbow)
    axis = wrist - shoulder
    reach = np.linalg.norm(axis)
    axis /= reach
    along = (upper_length**2 - lower_length**2 + reach**2) / (2 * reach)
    perpendicular = elbow_bias - axis * np.dot(elbow_bias, axis)
    perpendicular /= np.linalg.norm(perpendicular)
    elbow = shoulder + axis * along + perpendicular * np.sqrt(max(0, upper_length**2 - along**2))
    direction = direction / np.linalg.norm(direction)
    spread = spread - direction * np.dot(spread, direction)
    spread /= np.linalg.norm(spread)

    def swing_rotation(old_direction, new_direction):
        a = old_direction / np.linalg.norm(old_direction)
        b = new_direction / np.linalg.norm(new_direction)
        axis = np.cross(a, b)
        cosine = np.dot(a, b)
        cross_matrix = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        return np.eye(3) + cross_matrix + cross_matrix @ cross_matrix / max(1 + cosine, 1e-8)

    upper_orientation = swing_rotation(old_elbow - shoulder, elbow - shoulder) @ rest_pose[side + 'Arm'][:3, :3]
    lower_orientation = swing_rotation(old_wrist - old_elbow, wrist - elbow) @ rest_pose[side + 'ForeArm'][:3, :3]

    # Use landmarks from the actual hand surface. The inherited finger bones
    # are offset from several visible fingertips and are unsuitable landmarks.
    hand = candidate.prim('SM_Character_Hands')
    hand_points = candidate.arr(hand['attributes']['POSITION'])
    selected = np.flatnonzero(hand_points[:, 0] * (1 if side == 'Left' else -1) > 0)
    surface = hand_points[selected]
    center = surface.mean(axis=0)
    _, eigenvectors = np.linalg.eigh(np.cov(surface.T))
    long_axis = eigenvectors[:, 2]
    long_axis *= 1 if np.dot(long_axis, center - old_wrist) > 0 else -1
    across_axis = eigenvectors[:, 1]
    across_axis *= 1 if across_axis[2] > 0 else -1
    length_coordinate = (surface - center) @ long_axis
    width_coordinate = (surface - center) @ across_axis
    tip_indices = np.flatnonzero(length_coordinate > np.percentile(length_coordinate, 85))
    palm = (length_coordinate > np.percentile(length_coordinate, 35)) & (length_coordinate < np.percentile(length_coordinate, 80))
    high_indices = np.flatnonzero(palm & (width_coordinate > np.percentile(width_coordinate[palm], 70)))
    low_indices = np.flatnonzero(palm & (width_coordinate < np.percentile(width_coordinate[palm], 30)))
    sample_indices = np.concatenate([tip_indices, high_indices, low_indices])
    sample_points = np.column_stack([surface[sample_indices], np.ones(len(sample_indices))])
    joints = candidate.arr(hand['attributes']['JOINTS_0'])[selected[sample_indices]].astype(int)
    weights = candidate.arr(hand['attributes']['WEIGHTS_0'])[selected[sample_indices]]
    skin = candidate.g['skins'][0]
    inverse_bind = candidate.arr(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    joint_names = [node_data[index]['name'] for index in skin['joints']]

    def residual(angles):
        overrides = {name: angles[index * 3:index * 3 + 3] for index, name in enumerate(bone_names)}
        transforms = world(overrides, node_data)
        hand_position = transforms[side + 'Hand'][:3, 3]
        skin_matrices = np.array([transforms[name] @ inverse_bind[index] for index, name in enumerate(joint_names)])
        samples = np.einsum('nvij,nj,nv->ni', skin_matrices[joints], sample_points, weights)[:, :3]
        tip_end = len(tip_indices)
        high_end = tip_end + len(high_indices)
        long_axis = samples[:tip_end].mean(axis=0) - hand_position
        long_axis /= np.linalg.norm(long_axis)
        across = samples[tip_end:high_end].mean(axis=0) - samples[high_end:].mean(axis=0)
        across -= long_axis * np.dot(across, long_axis)
        across /= np.linalg.norm(across)
        return np.concatenate([(hand_position - wrist) * 60,
                               (transforms[side + 'ForeArm'][:3, 3] - elbow) * 45,
                               (long_axis - direction) * 2,
                               (across - spread) * 2,
                               (transforms[side + 'Arm'][:3, :3] - upper_orientation).ravel() * .6,
                               (transforms[side + 'ForeArm'][:3, :3] - lower_orientation).ravel() * .6,
                               (angles - initial) * .015])

    angles = initial.copy()
    damping = .01
    for _ in range(180):
        error = residual(angles)
        jacobian = np.empty((len(error), len(angles)))
        for index in range(len(angles)):
            shifted = angles.copy()
            shifted[index] += 1e-5
            jacobian[:, index] = (residual(shifted) - error) / 1e-5
        step = np.linalg.solve(jacobian.T @ jacobian + np.eye(len(angles)) * damping, -jacobian.T @ error)
        step *= min(1, .4 / max(np.linalg.norm(step), 1e-12))
        trial = angles + step
        if np.linalg.norm(residual(trial)) < np.linalg.norm(error):
            angles = trial
            damping = max(1e-6, damping * .5)
            if np.linalg.norm(step) < 1e-7:
                break
        else:
            damping *= 4
    result = {prefix + axis: round(float(angles[index * 3 + axis_index]), 6)
              for index, prefix in enumerate(prefixes) for axis_index, axis in enumerate('XYZ')}
    final = world({name: angles[index * 3:index * 3 + 3] for index, name in enumerate(bone_names)}, node_data)
    return result, {'wrist_error_mm': float(np.linalg.norm(final[side + 'Hand'][:3, 3] - wrist) * 1000),
                    'elbow_error_mm': float(np.linalg.norm(final[side + 'ForeArm'][:3, 3] - elbow) * 1000)}

poses, measurements = {}, {}
specifications = {
    'glasses_adjust': [('Right', [-.18, 1.51, .13], [.07, .085, -.035], [.035, 0, -.055], [-.65, -.7, .3])],
    'inspect_tablet': [('Right', [-.21, 1.12, .24], [.10, -.02, .07], [0, 0, 1], [-.35, -.8, -.6]),
                       ('Left', [.21, 1.12, .24], [-.10, -.02, .07], [0, 0, 1], [.35, -.8, -.6])],
    'keynote_present': [('Right', [-.37, 1.20, .24], [-.08, .05, .05], [.035, 0, .055], [-.2, -1, -.5])],
}
for label, arms in specifications.items():
    pose, rows = {}, {}
    for side, wrist, direction, spread, bias in arms:
        result, measurement = arm_fit(side, *[np.array(value, dtype=float) for value in (wrist, direction, spread, bias)])
        pose.update(result)
        rows[side] = measurement
    pose['fingerCurl'] = {'glasses_adjust': .15, 'inspect_tablet': .12, 'keynote_present': .04}[label]
    poses[label] = pose
    measurements[label] = rows
(root / 'work/poses27.json').write_text(json.dumps(poses, indent=2))
(root / 'work/poses27-fit.json').write_text(json.dumps(measurements, indent=2))
print(json.dumps(measurements))
