
# Each key is a named system check or category
# Each value is a dictionary of ---------------->  register: expected_value
REGISTER_CATEGORIES = {
    "startup": {
        0x2009: 0x0001,  # 
        0x621A: 0x0000,  # 
        0x6002: 0x0000,  # 
    },

    "homing_check": {
        0x6279: 0x0000,  # 
        0x627A: 0x0000,  # 
        0x6002: 0x0000,  # 
    },

    "alarm_status": {
        0x3001: 0x0000,  # 
        0x3002: 0x0000,  # 
    },
    # more categories can be added ...
}
