"""An isolated descriptor pool avoids collisions with older standalone bindings."""
from google.protobuf.descriptor_pool import DescriptorPool

POOL = DescriptorPool()
