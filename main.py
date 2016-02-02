import math

class Config(object):
    def __init__(self):
        self.file_name = "data.csv"
        self.query_file_name = "test_restaurant.csv"
        self.decision_header = "decision"
        self.decision_yes = 1
        self.decision_no = 0
        self.decisions_values = [self.decision_yes, self.decision_no]

def parse_csv_line(line):
    line = line.strip()
    splited_line = line.split(',')

    values = []
    for value in splited_line:
        values.append(value.strip())

    return values

def read_query(config):
    header, line = read_csv_file(config.query_file_name, config)
    return line

def read_csv_file(file_name, config):
    header = None
    lines = []

    with open(file_name, 'r') as f:
        for index, line in enumerate(f):
            if index == 0:
                header = parse_csv_line(line)
            else:
                lines.append(parse_csv_line(line))

    check_csv_data(header, lines, config)
    return header, lines

def read_data(config):
    return read_csv_file(config.file_name, config)

def get_header_types(header, lines):
    types = []
    for i in range(0, len(header)-1):
        types.append([])

    for line in lines:
        for index, value in enumerate(line):
            if index == len(header) - 1:
                break
            if value in types[index]:
                continue
            types[index].append(value)
    return types


def check_csv_data(header, lines, config=Config()):
    if header[-1].lower() != config.decision_header:
        raise Exception("Decision header is not valid in csv file!")

    for line in lines:
        try:
            line[-1] = int(line[-1])
            if line[-1] not in config.decisions_values:
                raise Exception("Line in cvs have invalid decision value")
        except ValueError:
            if line[-1] != "?":
                raise Exception("Line in cvs have invalid decision value")



def count_decisions(type, lines, column_index, config, lines_indexes):
    p_dict = {
        "yes": [],
        "no": []
    }

    for index, line in enumerate(lines):
        if index not in lines_indexes:
            continue

        if line[column_index] == type:
            if line[-1] == config.decision_yes:
                p_dict["yes"].append(index)
                continue

            if line[-1] == config.decision_no:
                p_dict["no"].append(index)
                continue
    return p_dict


def calculate_types_probability(headers, types, lines, config, lines_indexes):
    types_with_probability = get_dict_with_header_keys(headers)

    for column_index, type_list in enumerate(types):
        for type in type_list:
            count_dict = count_decisions(type, lines, column_index, config, lines_indexes)
            header_name = headers[column_index]
            types_with_probability[header_name][type] = count_dict

    return types_with_probability


def calculate_entropy(yes_count, no_count):
    if yes_count == 0 and no_count == 0:
        return -1

    if yes_count == 0 or no_count == 0:
        return 0

    number = float(sum([yes_count, no_count]))
    yes_probability = float(yes_count) / number
    no_probability = float(no_count) / number

    entropy = -yes_probability * math.log(yes_probability, 2) -no_probability*math.log(no_probability, 2)
    return entropy


def get_dict_with_header_keys(headers):
    last = len(headers) - 1
    result = {}
    for index, header in enumerate(headers):
        if index == last:
            break
        result[header] = {}

    return result


def calculate_types_entropies(headers, types, types_probability):
    types_entropy = get_dict_with_header_keys(headers)

    for column_index, type_list_in_types in enumerate(types):
        for subtype in type_list_in_types:
            header = headers[column_index]
            types_entropy[header][subtype] = calculate_entropy(len(types_probability[header][subtype]["yes"]), len(types_probability[header][subtype]["no"]))

    return types_entropy


def calculate_type_expected_value(header, type_list, types_probability, types_entropies, max_expected_value):
    expected_value = 0.0
    all_decisions = 0

    for subtype in type_list:
        all_decisions += len(types_probability[header][subtype]["yes"])
        all_decisions += len(types_probability[header][subtype]["no"])

    for subtype in type_list:
        if types_entropies[header][subtype] == -1:
            continue

        subtype_decisions = len(types_probability[header][subtype]["yes"]) + len(types_probability[header][subtype]["no"])
        probability = float(subtype_decisions) / float(all_decisions)
        expected_value +=  types_entropies[header][subtype] * (probability)

    return max_expected_value - expected_value


def check_expected_values_all_zeroes_or_minus_ones(array_list):
    should_break = True
    for element in array_list:
        if element not in [0, -1]:
            should_break = False
            break
            
    return should_break


def find_max_and_type_index(headers, types, types_entropies, value_list):
    max_value = max(value_list)
    max_index = value_list.index(max_value)

    header = headers[max_index]
    entropies = []
    for type in types[max_index]:
        entropies.append(types_entropies[header][type])

    return max(entropies), max_index


def get_lines_indexes(header, types_list, types_probability, types_entropies):
    result = []
    for type in types_list:
        if types_entropies[header][type] > 0 and types_entropies[header][type] <= 1:
            result += list(set(types_probability[header][type]['yes'] + types_probability[header][type]['no']))
            continue

    return result


def calculate_expected_values(headers, types, types_probability, types_entropies, config, lines):
    max_expected_value = 1
    expected_values_steps = []
    types_indexes_in_steps = []
    for i in range(0, len(types)):
        expected_values_steps.append([])

    types_entropies_steps = []
    types_probabilities_steps = []
    types_entropies_steps.append(types_entropies)
    types_probabilities_steps.append(types_probability)
    keep_going = len(types)
    column_index = 0
    while keep_going > 0:

        for types_index, type_list in enumerate(types):
            header = headers[types_index]
            expected_values_steps[column_index].append(calculate_type_expected_value(header, type_list, types_probability, types_entropies, max_expected_value))

        if column_index > 0:
            for index in types_indexes_in_steps:
                expected_values_steps[column_index][index] = -1


        max_value, subtype_index = find_max_and_type_index(headers, types, types_entropies, expected_values_steps[column_index])
        max_expected_value = max_value
        types_indexes_in_steps.append(subtype_index)

        if check_expected_values_all_zeroes_or_minus_ones(expected_values_steps[column_index]):
            break

        lines_indexes = get_lines_indexes(headers[subtype_index], types[subtype_index], types_probability, types_entropies)
        types_probability = calculate_types_probability(headers, types, lines, config, lines_indexes)
        types_entropies = calculate_types_entropies(headers, types, types_probability)

        types_probabilities_steps.append(types_probability)
        types_entropies_steps.append(types_entropies)

        column_index += 1
        keep_going -= 1

    return types_indexes_in_steps, types_probabilities_steps, types_entropies_steps


def print_tree(headers, types, types_indexes_in_steps, types_probabilities_steps, types_entropies_steps):
    print "=" * 30
    for step_index, header_index in enumerate(types_indexes_in_steps):
        header = headers[header_index]
        print "\t"*step_index, "H", header
        for subtype in types[header_index]:
            end_type = "-"
            if types_entropies_steps[step_index][header][subtype] == 0:
                if len(types_probabilities_steps[step_index][header][subtype]["yes"]) > 0:
                    end_type = "YES"
                if len(types_probabilities_steps[step_index][header][subtype]["no"]) > 0:
                    end_type = "NO"
            print "\t"*(step_index + 1), subtype, end_type
    print "=" * 30


def answer_to_queries(headers, types_indexes_in_steps, types_probabilities_steps, types_entropies_steps, queries):

    for query in queries:
        print "=" * 50
        print "Query:", query
        answer = "No"

        for step_index, header_index in enumerate(types_indexes_in_steps):
            header = headers[header_index]

            print "\t" * step_index, "(H)", header
            query_current_value = query[header_index]
            print "\t" * (step_index + 1), query_current_value
            if types_entropies_steps[step_index][header][query_current_value] == 0:
                if len(types_probabilities_steps[step_index][header][query_current_value]["yes"]) > 0:
                    answer = "YES"
                    break
                else:
                    answer = "NO"
                    break
            continue

        print "Should you go to restaurant? {0}".format(answer)
        print "=" * 50


def run():
    config = Config()
    headers, lines = read_data(config)
    queries = read_query(config)
    types = get_header_types(headers, lines)

    lines_indexes = [x for x in range(0, len(lines))]
    types_probability = calculate_types_probability(headers, types, lines, config, lines_indexes)
    types_entropies = calculate_types_entropies(headers, types, types_probability)
    types_indexes_in_steps, types_probabilities_steps, types_entropies_steps = calculate_expected_values(headers, types, types_probability, types_entropies, config, lines)

    print_tree(headers, types, types_indexes_in_steps, types_probabilities_steps, types_entropies_steps)
    answer_to_queries(headers, types_indexes_in_steps, types_probabilities_steps, types_entropies_steps, queries)
run()