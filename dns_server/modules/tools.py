class Tools:
    @staticmethod
    def get_label_list(url):
        label_list = url.split('.')
        if label_list[0] == 'www':
            label_list.remove('www')
        return label_list

    @staticmethod
    def get_url(label_list):
        return '.'.join(label_list)

    @staticmethod
    def get_labels_string(label_list):
        labels_string = b''
        for label in label_list:
            label_b = label.encode('idna')
            length_b = len(label_b).to_bytes(1, 'big')
            labels_string += length_b + label_b
        labels_string += int(0).to_bytes(1, 'big')
        return labels_string

    @staticmethod
    def parse_binary_labels(labels_b):
        labels = []
        label_len = labels_b[0]
        while label_len != 0:
            label = labels_b[1:label_len + 1]
            labels_b = labels_b[label_len + 1:]
            label_len = labels_b[0]
            labels.append(label.decode('idna'))
        return labels, labels_b[1:]

    @staticmethod
    def parse_name(data, total_data):
        labels = []
        label_len = data[0]
        while label_len != 0:
            if f'{label_len:08b}'[0:2] == '11':
                name_pointer = int(f'{data[0]:08b}'[2:] + f'{data[1]:08b}', 2)
                more_labels, _ = Tools.parse_name(total_data[name_pointer:], total_data)
                labels.extend(more_labels)
                data = data[1:]
                break
            label = data[1:label_len + 1]
            data = data[label_len + 1:]
            label_len = data[0]
            labels.append(label.decode('idna'))
        return labels, data[1:]
