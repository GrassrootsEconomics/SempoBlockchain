import enum
from sqlalchemy.sql import text
from sqlalchemy import or_, Column, String, Float
from server import db
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.models.transfer_account import TransferAccount
from server.models.user import User
from sqlalchemy.sql.expression import cast

MALE = 'male'
FEMALE = 'female'

BENEFICIARY = 'has_beneficiary_role'
VENDOR = 'has_vendor_role'
TOKEN_AGENT = 'has_token_agent_role'
GROUP_ACCOUNT = 'has_group_account_role'

class TransferFilterEnum:
    INT_RANGE       = "int_range"
    DATE_RANGE      = 'date_range'
    DISCRETE        = "discrete"
    BOOLEAN_MAPPING = "boolean_mapping"

TRANSFER_FILTERS = {
    'created': {
        'table': User.__tablename__,
        'type' : TransferFilterEnum.DATE_RANGE,
    },
    'User Type': {
        'table': User.__tablename__,
        'type': TransferFilterEnum.BOOLEAN_MAPPING,
        'values': [BENEFICIARY, VENDOR, TOKEN_AGENT, GROUP_ACCOUNT]
    },
    'gender': {
        'table': CustomAttributeUserStorage.__tablename__,
        'type': TransferFilterEnum.DISCRETE,
        'values' : [MALE, FEMALE]
    },
    'account_balance': {
        'table': TransferAccount.__tablename__,
        'type' : TransferFilterEnum.INT_RANGE
    }
}

# will return a dictionary with table names as keys
# values will be a dictionary of array of tuples
# values on the outer array should be AND'd together

# {
#     users: [(keyname, operator, value), (keyname, operator, value)],
#     customuserattributes: [(gender, =, male),(gender, =, female), (age, =, 25)],
#     transferaccounts: [(balance, >, 0), (keyname, operator, value)]
# }

def process_transfer_filters(encoded_filters):
    # parse and prepare filters for calculating transfer stats
    tokenized_filters = encoded_filters.split("%")
    filters = {}
    curr_keyName = None

    to_handle = []
    for item in tokenized_filters:
        if item is not None and len(item) > 0:
            symbol = item[:1]
            subject = item[1:]
            if symbol == ",":

                # handle currently collected filters
                filters = handle_filters_per_keyname(to_handle, curr_keyName, filters)

                curr_keyName = None
                if subject in TRANSFER_FILTERS:
                    to_handle = []
                    curr_keyName = subject
            if (symbol == "=" or symbol == "<" or symbol == ">"):
                to_handle.append({
                    'comparator': symbol,
                    'value': subject
                })

    # handle currently collected filters
    filters = handle_filters_per_keyname(to_handle, curr_keyName, filters)
    print(filters)
    return filters

def handle_filters_per_keyname(to_handle, key_name, filters):
    if len(to_handle) > 0 and (key_name is not None):
        curr_table = TRANSFER_FILTERS[key_name]['table']
        if(curr_table == CustomAttributeUserStorage.__tablename__):
            _filters = filters[curr_table] if curr_table in filters and isinstance(filters[curr_table], list) else []
            _filters.append(handle_custom_user_storage_filter(key_name, to_handle))
            filters[curr_table] = _filters
        else:
            _filters = filters[curr_table] if curr_table in filters and isinstance(filters[curr_table], list) else []
            _filters.append(handle_filter(key_name, to_handle))
            filters[curr_table] = _filters
    return filters

# assemble filters 
def handle_custom_user_storage_filter(keyname, filters):
    formatted_filters = []
    i = 0
    while i < len(filters):
        filter_action = filters[i]
        comparator = filter_action['comparator']
        val = filter_action['value']

        equals_in = []
        while i < len(filters) and filters[i]['comparator'] == '=':
            filter_action = filters[i]
            comparator = filter_action['comparator']
            val = filter_action['value']
            equals_in.append(val)
            i += 1

        if len(equals_in) > 0:
            formatted_filters.append((keyname, "EQ", equals_in))
        elif comparator == '>':
            formatted_filters.append((keyname, "GT", val))
        elif comparator == '<':
            formatted_filters.append((keyname, "LT", val))
        else:
            return
        i += 1
    return formatted_filters

def handle_filter(keyname, filters):

    if TRANSFER_FILTERS[keyname]['type'] == TransferFilterEnum.BOOLEAN_MAPPING:
        return handle_boolean_mapping(keyname, filters)
    elif TRANSFER_FILTERS[keyname]['type'] == TransferFilterEnum.DISCRETE:
        return handle_discrete(keyname, filters)
    else:
        return handle_other_types(keyname, filters)

def handle_boolean_mapping(keyname, filters):
    formatted_filters = []
    for _filt in filters:
        comparator = _filt['comparator']
        val = _filt['value']
        formatted_filters.append((val, "EQ", True))
    print(formatted_filters)
    return formatted_filters

def handle_discrete(keyname, filters):

    equals_in = []
    i = 0
    while i < len(filters):
        filter_action = filters[i]
        comparator = filter_action['comparator']
        val = filter_action['value']
        equals_in.append(val)
        i += 1
    return [(keyname, "EQ", equals_in)]

def handle_other_types(keyname, filters):
    formatted_filters = []
    table = get_class_by_tablename(TRANSFER_FILTERS[keyname]['table'])
    column = getattr(table, keyname)
    
    i = 0
    while i < len(filters):
        filter_action = filters[i]
        comparator = filter_action['comparator']
        val = filter_action['value']

        if comparator == '>':
            formatted_filters.append((keyname, "GT", val if column.type == 'DATETIME' else float(val)))
        elif comparator == '<':
            formatted_filters.append((keyname, "LT", val if column.type == 'DATETIME' else float(val)))
        else:
            return

        i += 1
    return formatted_filters

def get_class_by_tablename(tablename):
  """Return class reference mapped to table.

  :param tablename: String with name of table.
  :return: Class reference or None.
  """
  for c in db.Model._decl_class_registry.values():
    if hasattr(c, '__tablename__') and c.__tablename__ == tablename:
      return c