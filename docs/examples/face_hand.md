# Face and Hand Data

Current App outputs are independent: [face data on 8102](face.md) and [hand data on 8101](hand.md). Use `FaceDataSubscriber` and `HandPoseDataSubscriber`, respectively. The legacy `FaceAndHandTrackingDataSubscriber` decodes combined frames from older App builds only; current App output has no nested hands.
