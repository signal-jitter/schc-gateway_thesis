RULE_PING_REQ = {\
             "ruleid"  : 6,
             "content" : [["IPv6.version",      1, "bi", 6,         "equal",  "not-sent"],
                          ["IPv6.trafficClass", 1, "bi", 0x00,      "equal",  "not-sent"],
                          ["IPv6.flowLabel",    1, "bi", 0x000000,  "ignore", "not-sent"],
                          ["IPv6.payloadLength",1, "bi", None,      "ignore", "compute-length"],
                          ["IPv6.nextHeader",   1, "bi", 58,        "equal",  "not-sent"],
                          ["IPv6.hopLimit",     1, "bi", 40,        "ignore", "not-sent"],
                          ["IPv6.prefixES",     1, "bi", 0x200108D8180184DD,      "equal", "not-sent"],
                          ["IPv6.iidES",        1, "bi", 0x0000000000000001,      "ignore", "value-sent"],
                          ["IPv6.prefixLA",     1, "bi", 0xFE80000000000000,      "ignore", "value-sent"],
                          ["IPv6.iidLA",        1, "bi", 0x0000000000000002,      "ignore", "value-sent"],
                          ["ICMPV6.TYPE",       1, "bi", 128,       "equal",  "not-sent"],
                          ["ICMPV6.CODE",       1, "bi", 0,         "equal",  "not-sent"],
                          ["ICMPV6.CKSUM",      1, "bi", 0,         "ignore", "compute-length"],
                          ["ICMPV6.IDENT",      1, "bi", 0,         "ignore", "value-sent"],
                          ["ICMPV6.SEQNO",      1, "bi", 0,         "ignore", "value-sent"],
                         ]
                    }

RULE_PING_RESP = {\
             "ruleid"  : 7,
             "content" : [["IPv6.version",      1, "bi", 6,         "equal",  "not-sent"],
                          ["IPv6.trafficClass", 1, "bi", 0x00,      "equal",  "not-sent"],
                          ["IPv6.flowLabel",    1, "bi", 0x000000,  "ignore", "not-sent"],
                          ["IPv6.payloadLength",1, "bi", None,      "ignore", "compute-length"],
                          ["IPv6.nextHeader",   1, "bi", 58,        "equal",  "not-sent"],
                          ["IPv6.hopLimit",     1, "bi", 40,        "ignore", "not-sent"],
                          ["IPv6.prefixES",     1, "bi", 0x200108D8180184DD,      "equal", "not-sent"],
                          ["IPv6.iidES",        1, "bi", 0x0000000000000001,      "ignore", "value-sent"],
                          ["IPv6.prefixLA",     1, "bi", 0xFE80000000000000,      "ignore", "value-sent"],
                          ["IPv6.iidLA",        1, "bi", 0x0000000000000002,      "ignore", "value-sent"],
                          ["ICMPV6.TYPE",       1, "bi", 129,       "equal",  "not-sent"],
                          ["ICMPV6.CODE",       1, "bi", 0,         "equal",  "not-sent"],
                          ["ICMPV6.CKSUM",      1, "bi", 0,         "ignore", "compute-length"],
                          ["ICMPV6.IDENT",      1, "bi", 0,         "ignore", "value-sent"],
                          ["ICMPV6.SEQNO",      1, "bi", 0,         "ignore", "value-sent"],
                         ]
                    }
