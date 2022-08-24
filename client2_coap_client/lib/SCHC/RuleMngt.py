import re
import struct

def MO_ignore( TV, FV, length, arg = None ):
    """Matching Operator ignore, return true for any Target Value"""
#    print( "\tignore" )
    return True

def MO_equal( TV, FV, length, arg = None ):
    """"Matching Operator equal. Compare Target Value and Field Value,
    return False if type are different or if value are different. """
    # print( "\tequal ", type( TV ), ' ', type( FV ) )
    if ( type( TV ) != type( FV ) ):
        return False
    return TV == FV

def MO_matchmapping( TV, FV, length, arg = None ):
    """Matching Operator match-mapping, can be used with number and string.
    length is given is bits, arg is not used.
    Target value can either be list or dictionnary, return True if the
    FV is found in one element of the TV.
    """
    # print( "\tmatch-mapping", type(TV))
    if type(TV) is dict:
        for mappingID, mappingValue in TV.items():
            if mappingValue == FV:
                return True
        return False
    elif type(TV) is list:
        for mappingValue in TV:
            # print ('\t', type (mappingValue), '  <=> ', type (FV), end='|')
            # print ('\t', mappingValue, '  <=> ', FV)
            if type(mappingValue) != type (FV):
                return False
            if mappingValue == FV:
                return True
        return False
    else:
        return False

def MO_MSB( TV, FV, length, arg = None ):
    """Matching Operator MSB (Most Significant Bits)
    - accept string and numbers
    - length is the size of field and arg is the number of bits that should be
    checked.

    return true if the left arg bits are the same in TV and FV """

    print( "\tMSB ", type( TV ), ' ', type( FV ), "FV length =", length, ' arg =', arg )
# dont work on quite long, may be we shouls add this for prefixES

    if (type(TV) != type(FV)):
        return False

    if (arg == None):
        print("length must be provided")
        return False

    if type(FV) is int:
        # print('lets do bitmap from int')
        TVbitmap = struct.pack("!L", TV)
        FVbitmap = struct.pack("!L", FV)

        arg += 32 - length  # since every number is stored on 32 bits
                            # the size to test is adjusted is the FV is smaller
                            # in size

    elif type(TV) is str:
        TVbitmap = bytearray(TV)
        FVbitmap = bytearray(FV)
    else:
        print ('unkwown type ', type(FV))
        return False

#    print (TVbitmap, '<===>', FVbitmap)

    idx = 0
    while arg > 0:
        if arg >= 8: # compare a char
            if (TVbitmap[idx] != FVbitmap[idx]):
                return False
            idx += 1
            arg -= 8
        else:
            msk = 1 << (8-arg)
            if ((TVbitmap[idx] & msk) != (FVbitmap[idx] & msk)): return False
            arg -= 1
    return True

class RuleManager:
    """This class is used to store rules and retrieve then either by looking
    at the rule number or field description.
    A rule is a JSON dictionnary containing:
    - "ruleid" : rule number.
    - "devid" : used by the infra SCHC C/D, not mandatory on device.
    - "content" : a list (array) of fields description.
    - "upRules" and "downRules": automatically computed when the rule is stored."""

    def __init__(self):
        self.context = []
        self.MatchingOperators = {
            "ignore": MO_ignore,
            "equal" : MO_equal,
            "match-mapping" : MO_matchmapping,
            "MSB" : MO_MSB
        }

    def addRule (self, rule):
        """Add a rule to the context, ruleid must be unique """
        addedRuleID = rule["ruleid"]
        for r in self.context:
            if (r["ruleid"] == addedRuleID):
                raise ValueError ('Rule ID already exists ', addedRuleID)

        self.context.append(rule)

        up = 0;
        down = 0;
        for entry in rule["content"]:
            if (entry[2] == "bi") or (entry[2] == "dw"): down += 1
            if (entry[2] == "bi") or (entry[2] == "up"): up += 1

        #print(self.context)
        #        print ('up =', up, ' down = ', down)
        rule["upRules"] = up
        rule["downRules"] = down

    def FindRuleFromID (self, ruleid):
        """ Find a rule form a Rule ID.
        take into argument a ruleid and return the appropriate rule. """
        for x in self.context:
            if x["ruleid"] == ruleid:
                return x


        return None

    def FindRuleFromHeader(self, headers, direction):
        """Find a Rule from a header description given by a parser.
        direction should be "up" or "down"  """
        for rule in self.context:
            #print('applying rule ', rule)

            print("looking for size ", len(headers)," ", rule["upRules"], ' ', rule["downRules"])
            #not the good number of rules, try the next
            if (direction == "up" and len(headers) != rule["upRules"]): continue
            if (direction == "dw" and len(headers) != rule["downRules"]): continue

            # Looking MO
            foundEntries = 0
            for entry in rule["content"]:
                FID = entry[0]
                POS = entry[1]

                DI = entry [2]
                if (DI == "bi") or (DI==direction):

                    try:
                        FV = headers[FID, POS][0]
                    except:
                        print('Field not found in rule')
                        break

                    foundEntries += 1
                    TV = entry[3]
                    MO = entry[4]
                    fieldLength = headers[FID, POS][1]

                    # does the MO has an argument
                    arg = None
                    reg = re.search('\((.*)\)', MO)
                    if reg:
                        # group(1) returns the first parenthesized subgroup
                        arg = int(reg.group(1))
                        MO = MO.split('(')[0] # remove the argument and parentheses
                        MO = MO.replace (' ', '') # suppress blank if any

# MO must be cleaned of argument MSB(4) => MSB and arg = 4
                    print (' {1:3d} {2:15s} Call {0:10s} TV = '.format(MO, foundEntries, FID), TV, ' FV = ', FV)
                    if (not self.MatchingOperators[MO](TV, FV, fieldLength, arg)):
                        break

            print("Found ", foundEntries, " among ", len(headers), ' ', rule["upRules"], ' ', rule["downRules"])
            if (direction == "up" and foundEntries == rule["upRules"]):
                  return rule
            if (direction == "dw" and foundEntries == rule["downRules"]):
                  return rule

        print ("No rule matches header")
        return (None)
