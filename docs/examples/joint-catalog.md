# Joint names, enums and typed attributes

Select one person from `frame.people`, then use the paths below to read their joints. Rows match `person.skeleton()` for each model; use `layout="common"` for the twelve shared rows.

Left and right refer to the person's own body. Missing joints return `None`; unavailable array values keep their rows with NaN and a false validity flag.

[Body examples](body.md) · [Hand examples](hand.md) · [Data format and API](api-reference.md)

## Common body: twelve fixed rows

| Row | Read with | Location |
|---:|---|---|
| 0 | `person.joints.left_shoulder` | Left shoulder |
| 1 | `person.joints.right_shoulder` | Right shoulder |
| 2 | `person.joints.left_elbow` | Left elbow |
| 3 | `person.joints.right_elbow` | Right elbow |
| 4 | `person.joints.left_wrist` | Left wrist |
| 5 | `person.joints.right_wrist` | Right wrist |
| 6 | `person.joints.left_hip` | Left hip |
| 7 | `person.joints.right_hip` | Right hip |
| 8 | `person.joints.left_knee` | Left knee |
| 9 | `person.joints.right_knee` | Right knee |
| 10 | `person.joints.left_ankle` | Left ankle |
| 11 | `person.joints.right_ankle` | Right ankle |

## MediaPipe: 33 landmarks

Rows match the default 33-joint skeleton array. All positions are preserved, including low-score estimates; joint rotations are unavailable.

| Row | Read with | Location |
|---:|---|---|
| 0 | `person.joints.nose` | Nose |
| 1 | `person.joints.left_eye_inner` | Left eye inner |
| 2 | `person.joints.left_eye` | Left eye |
| 3 | `person.joints.left_eye_outer` | Left eye outer |
| 4 | `person.joints.right_eye_inner` | Right eye inner |
| 5 | `person.joints.right_eye` | Right eye |
| 6 | `person.joints.right_eye_outer` | Right eye outer |
| 7 | `person.joints.left_ear` | Left ear |
| 8 | `person.joints.right_ear` | Right ear |
| 9 | `person.joints.mouth_left` | Left mouth corner |
| 10 | `person.joints.mouth_right` | Right mouth corner |
| 11 | `person.joints.left_shoulder` | Left shoulder |
| 12 | `person.joints.right_shoulder` | Right shoulder |
| 13 | `person.joints.left_elbow` | Left elbow |
| 14 | `person.joints.right_elbow` | Right elbow |
| 15 | `person.joints.left_wrist` | Left wrist |
| 16 | `person.joints.right_wrist` | Right wrist |
| 17 | `person.joints.left_pinky` | Left little-finger landmark |
| 18 | `person.joints.right_pinky` | Right little-finger landmark |
| 19 | `person.joints.left_index` | Left index-finger landmark |
| 20 | `person.joints.right_index` | Right index-finger landmark |
| 21 | `person.joints.left_thumb` | Left thumb landmark |
| 22 | `person.joints.right_thumb` | Right thumb landmark |
| 23 | `person.joints.left_hip` | Left hip |
| 24 | `person.joints.right_hip` | Right hip |
| 25 | `person.joints.left_knee` | Left knee |
| 26 | `person.joints.right_knee` | Right knee |
| 27 | `person.joints.left_ankle` | Left ankle |
| 28 | `person.joints.right_ankle` | Right ankle |
| 29 | `person.joints.left_heel` | Left heel |
| 30 | `person.joints.right_heel` | Right heel |
| 31 | `person.joints.left_foot_index` | Left forefoot landmark |
| 32 | `person.joints.right_foot_index` | Right forefoot landmark |

## ARKit: 91 joints

Rows match the default 91-joint skeleton array. Some joint transforms are estimated; check the joint's tracked flag when direct observation matters. Numbered finger, spine and neck points follow ARKit's skeleton segments; they are not additional people or detection scores.

| Row | Read with | Location |
|---:|---|---|
| 0 | `person.joints.root` | Body root |
| 1 | `person.joints.hips` | Pelvis |
| 2 | `person.joints.left_hip` | Left hip |
| 3 | `person.joints.left_knee` | Left knee |
| 4 | `person.joints.left_ankle` | Left ankle |
| 5 | `person.joints.left_toes` | Left toes |
| 6 | `person.joints.left_toes_end` | Left toes end |
| 7 | `person.joints.right_hip` | Right hip |
| 8 | `person.joints.right_knee` | Right knee |
| 9 | `person.joints.right_ankle` | Right ankle |
| 10 | `person.joints.right_toes` | Right toes |
| 11 | `person.joints.right_toes_end` | Right toes end |
| 12 | `person.joints.spine_1` | Spine 1 |
| 13 | `person.joints.spine_2` | Spine 2 |
| 14 | `person.joints.spine_3` | Spine 3 |
| 15 | `person.joints.spine_4` | Spine 4 |
| 16 | `person.joints.spine_5` | Spine 5 |
| 17 | `person.joints.spine_6` | Spine 6 |
| 18 | `person.joints.spine_7` | Spine 7 |
| 19 | `person.joints.left_shoulder_1` | Left shoulder 1 |
| 20 | `person.joints.left_shoulder` | Left shoulder |
| 21 | `person.joints.left_elbow` | Left elbow |
| 22 | `person.joints.left_wrist` | Left wrist |
| 23 | `person.joints.left_hand_index_start` | Left index finger start |
| 24 | `person.joints.left_hand_index_1` | Left index finger 1 |
| 25 | `person.joints.left_hand_index_2` | Left index finger 2 |
| 26 | `person.joints.left_hand_index_3` | Left index finger 3 |
| 27 | `person.joints.left_hand_index_end` | Left index finger end |
| 28 | `person.joints.left_hand_mid_start` | Left middle finger start |
| 29 | `person.joints.left_hand_mid_1` | Left middle finger 1 |
| 30 | `person.joints.left_hand_mid_2` | Left middle finger 2 |
| 31 | `person.joints.left_hand_mid_3` | Left middle finger 3 |
| 32 | `person.joints.left_hand_mid_end` | Left middle finger end |
| 33 | `person.joints.left_hand_pinky_start` | Left little finger start |
| 34 | `person.joints.left_hand_pinky_1` | Left little finger 1 |
| 35 | `person.joints.left_hand_pinky_2` | Left little finger 2 |
| 36 | `person.joints.left_hand_pinky_3` | Left little finger 3 |
| 37 | `person.joints.left_hand_pinky_end` | Left little finger end |
| 38 | `person.joints.left_hand_ring_start` | Left ring finger start |
| 39 | `person.joints.left_hand_ring_1` | Left ring finger 1 |
| 40 | `person.joints.left_hand_ring_2` | Left ring finger 2 |
| 41 | `person.joints.left_hand_ring_3` | Left ring finger 3 |
| 42 | `person.joints.left_hand_ring_end` | Left ring finger end |
| 43 | `person.joints.left_hand_thumb_start` | Left thumb start |
| 44 | `person.joints.left_hand_thumb_1` | Left thumb 1 |
| 45 | `person.joints.left_hand_thumb_2` | Left thumb 2 |
| 46 | `person.joints.left_hand_thumb_end` | Left thumb end |
| 47 | `person.joints.neck_1` | Neck 1 |
| 48 | `person.joints.neck_2` | Neck 2 |
| 49 | `person.joints.neck_3` | Neck 3 |
| 50 | `person.joints.neck_4` | Neck 4 |
| 51 | `person.joints.head` | Head |
| 52 | `person.joints.jaw` | Jaw |
| 53 | `person.joints.chin` | Chin |
| 54 | `person.joints.left_eye` | Left eye |
| 55 | `person.joints.left_eye_lower_lid` | Left eye lower lid |
| 56 | `person.joints.left_eye_upper_lid` | Left eye upper lid |
| 57 | `person.joints.left_eyeball` | Left eyeball |
| 58 | `person.joints.nose` | Nose |
| 59 | `person.joints.right_eye` | Right eye |
| 60 | `person.joints.right_eye_lower_lid` | Right eye lower lid |
| 61 | `person.joints.right_eye_upper_lid` | Right eye upper lid |
| 62 | `person.joints.right_eyeball` | Right eyeball |
| 63 | `person.joints.right_shoulder_1` | Right shoulder 1 |
| 64 | `person.joints.right_shoulder` | Right shoulder |
| 65 | `person.joints.right_elbow` | Right elbow |
| 66 | `person.joints.right_wrist` | Right wrist |
| 67 | `person.joints.right_hand_index_start` | Right index finger start |
| 68 | `person.joints.right_hand_index_1` | Right index finger 1 |
| 69 | `person.joints.right_hand_index_2` | Right index finger 2 |
| 70 | `person.joints.right_hand_index_3` | Right index finger 3 |
| 71 | `person.joints.right_hand_index_end` | Right index finger end |
| 72 | `person.joints.right_hand_mid_start` | Right middle finger start |
| 73 | `person.joints.right_hand_mid_1` | Right middle finger 1 |
| 74 | `person.joints.right_hand_mid_2` | Right middle finger 2 |
| 75 | `person.joints.right_hand_mid_3` | Right middle finger 3 |
| 76 | `person.joints.right_hand_mid_end` | Right middle finger end |
| 77 | `person.joints.right_hand_pinky_start` | Right little finger start |
| 78 | `person.joints.right_hand_pinky_1` | Right little finger 1 |
| 79 | `person.joints.right_hand_pinky_2` | Right little finger 2 |
| 80 | `person.joints.right_hand_pinky_3` | Right little finger 3 |
| 81 | `person.joints.right_hand_pinky_end` | Right little finger end |
| 82 | `person.joints.right_hand_ring_start` | Right ring finger start |
| 83 | `person.joints.right_hand_ring_1` | Right ring finger 1 |
| 84 | `person.joints.right_hand_ring_2` | Right ring finger 2 |
| 85 | `person.joints.right_hand_ring_3` | Right ring finger 3 |
| 86 | `person.joints.right_hand_ring_end` | Right ring finger end |
| 87 | `person.joints.right_hand_thumb_start` | Right thumb start |
| 88 | `person.joints.right_hand_thumb_1` | Right thumb 1 |
| 89 | `person.joints.right_hand_thumb_2` | Right thumb 2 |
| 90 | `person.joints.right_hand_thumb_end` | Right thumb end |

## 2D hand: 21 joints

| Row | Enum | Wire name | Typed access |
|---:|---|---|---|
| 0 | `HandJointName.WRIST` | `wrist` | `hand.joints.wrist` |
| 1 | `HandJointName.THUMB_CMC` | `thumb_cmc` | `hand.joints.thumb_cmc` |
| 2 | `HandJointName.THUMB_MP` | `thumb_mp` | `hand.joints.thumb_mp` |
| 3 | `HandJointName.THUMB_IP` | `thumb_ip` | `hand.joints.thumb_ip` |
| 4 | `HandJointName.THUMB_TIP` | `thumb_tip` | `hand.joints.thumb_tip` |
| 5 | `HandJointName.INDEX_MCP` | `index_mcp` | `hand.joints.index_mcp` |
| 6 | `HandJointName.INDEX_PIP` | `index_pip` | `hand.joints.index_pip` |
| 7 | `HandJointName.INDEX_DIP` | `index_dip` | `hand.joints.index_dip` |
| 8 | `HandJointName.INDEX_TIP` | `index_tip` | `hand.joints.index_tip` |
| 9 | `HandJointName.MIDDLE_MCP` | `middle_mcp` | `hand.joints.middle_mcp` |
| 10 | `HandJointName.MIDDLE_PIP` | `middle_pip` | `hand.joints.middle_pip` |
| 11 | `HandJointName.MIDDLE_DIP` | `middle_dip` | `hand.joints.middle_dip` |
| 12 | `HandJointName.MIDDLE_TIP` | `middle_tip` | `hand.joints.middle_tip` |
| 13 | `HandJointName.RING_MCP` | `ring_mcp` | `hand.joints.ring_mcp` |
| 14 | `HandJointName.RING_PIP` | `ring_pip` | `hand.joints.ring_pip` |
| 15 | `HandJointName.RING_DIP` | `ring_dip` | `hand.joints.ring_dip` |
| 16 | `HandJointName.RING_TIP` | `ring_tip` | `hand.joints.ring_tip` |
| 17 | `HandJointName.LITTLE_MCP` | `little_mcp` | `hand.joints.little_mcp` |
| 18 | `HandJointName.LITTLE_PIP` | `little_pip` | `hand.joints.little_pip` |
| 19 | `HandJointName.LITTLE_DIP` | `little_dip` | `hand.joints.little_dip` |
| 20 | `HandJointName.LITTLE_TIP` | `little_tip` | `hand.joints.little_tip` |
