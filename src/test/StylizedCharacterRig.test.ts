import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as THREE from 'three';
import { StylizedCharacterRig } from '../graphics/persona/StylizedCharacterRig';

describe('StylizedCharacterRig Test Suite', () => {
  let rig: StylizedCharacterRig;

  beforeEach(() => {
    rig = new StylizedCharacterRig();
  });

  afterEach(() => {
    rig.dispose();
  });

  it('instantiates successfully with hierarchical bone groups', () => {
    expect(rig.group).toBeInstanceOf(THREE.Group);
    expect(rig.hips).toBeInstanceOf(THREE.Group);
    expect(rig.spine).toBeInstanceOf(THREE.Group);
    expect(rig.neck).toBeInstanceOf(THREE.Group);
    expect(rig.headPivot).toBeInstanceOf(THREE.Group);
  });

  it('constructs personal signature tokens: hoodie, titanium spectacles, curtain bangs', () => {
    // Hoodie Cowl and Pocket
    expect(rig.hoodCowl).toBeInstanceOf(THREE.Mesh);
    expect(rig.kangarooPocket).toBeInstanceOf(THREE.Mesh);

    // Hairstyle
    expect(rig.hairCap).toBeInstanceOf(THREE.Mesh);
    expect(rig.leftBang).toBeInstanceOf(THREE.Mesh);
    expect(rig.rightBang).toBeInstanceOf(THREE.Mesh);

    // Glasses Group
    expect(rig.glassesGroup).toBeInstanceOf(THREE.Group);
    expect(rig.glassesGroup.children.length).toBeGreaterThanOrEqual(5); // left rim, left lens, right rim, right lens, bridge, temples
  });

  it('constructs fully articulated limb hierarchy with shoulders, elbows, wrists, hips, knees, ankles', () => {
    // Left Arm
    expect(rig.leftShoulder).toBeInstanceOf(THREE.Group);
    expect(rig.leftElbow).toBeInstanceOf(THREE.Group);
    expect(rig.leftWrist).toBeInstanceOf(THREE.Group);
    expect(rig.leftHand).toBeInstanceOf(THREE.Mesh);

    // Right Arm
    expect(rig.rightShoulder).toBeInstanceOf(THREE.Group);
    expect(rig.rightElbow).toBeInstanceOf(THREE.Group);
    expect(rig.rightWrist).toBeInstanceOf(THREE.Group);
    expect(rig.rightHand).toBeInstanceOf(THREE.Mesh);

    // Left Leg
    expect(rig.leftHip).toBeInstanceOf(THREE.Group);
    expect(rig.leftKnee).toBeInstanceOf(THREE.Group);
    expect(rig.leftAnkle).toBeInstanceOf(THREE.Group);
    expect(rig.leftSneaker).toBeInstanceOf(THREE.Mesh);

    // Right Leg
    expect(rig.rightHip).toBeInstanceOf(THREE.Group);
    expect(rig.rightKnee).toBeInstanceOf(THREE.Group);
    expect(rig.rightAnkle).toBeInstanceOf(THREE.Group);
    expect(rig.rightSneaker).toBeInstanceOf(THREE.Mesh);
  });

  it('supports setting all storyline and dynamic postures and updates active state', () => {
    const postures = [
      'idle',
      'seated',
      'walk',
      'reach_book',
      'conduct_badges',
      'climb_ridge',
      'hoist_trophy',
      'operate_core',
      'wave',
      'glasses_adjust',
      'inspect_tablet',
      'keynote_present',
    ] as const;

    for (const posture of postures) {
      rig.setPosture(posture);
      expect(rig.getActivePosture()).toBe(posture);
    }
  });

  it('attaches and displays the 24k Gold Trophy when in hoist_trophy posture', () => {
    rig.setPosture('idle');
    expect(rig.heldTrophy.visible).toBe(false);

    rig.setPosture('hoist_trophy');
    expect(rig.heldTrophy.visible).toBe(true);
  });

  it('executes update loop with natural breathing, cursor lookat, and smooth damping', () => {
    expect(() => {
      rig.update(0.016, 0.5, -0.3);
      rig.update(0.016, 0.0, 0.0);
    }).not.toThrow();
  });

  it('executes walk cycle locomotion without errors', () => {
    rig.setPosture('walk');
    expect(() => {
      for (let i = 0; i < 20; i++) {
        rig.update(0.016, 0, 0);
      }
    }).not.toThrow();
  });

  it('disposes all materials and geometries cleanly without throwing', () => {
    expect(() => {
      rig.dispose();
    }).not.toThrow();
  });
});
