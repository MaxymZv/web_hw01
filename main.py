from abc import ABC, abstractmethod
from collections import UserDict
from datetime import datetime, timedelta
from functools import wraps
import pickle

# Making class Field that will be used as a base class for Name and Phone
class Field:
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


# Making class Phone 
class Phone(Field):
    def __init__(self, value):
        value = str(value)
        if not (value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must be a 10-digit number.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        # verification of date format
        if isinstance(value, str):
            try:
                # verification if we can parse the date
                datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                raise ValueError("Birthday must be in the format 'DD.MM.YYYY'.")
            super().__init__(value)  # Зберігаємо як рядок
        else:
            raise ValueError("Birthday must be a string in format 'DD.MM.YYYY'.")


# Making class Record that will hold contact information
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def __str__(self):
        return f'Contact name: {self.name.value}, Phones: {",".join(str(p) for p in self.phones)}'
    
    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)
    
    def get_birthday(self):
        if self.birthday:
            return self.birthday.value
        return None

    # Method for adding phone number    
    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    # Method for removing phone number
    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return
        raise ValueError(f"Phone number {phone} not found in record.")

    # Method for editing phone number
    def edit_phone(self, old_phone, new_phone):
        for index, phone in enumerate(self.phones):
            if phone.value == old_phone:
                self.phones[index] = Phone(new_phone)
                return
        raise ValueError(f"Phone number {old_phone} not found in record.") 

    # Method for finding phone number 
    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None


# Making class Adressbook that inherits from UserDict    
class AddressBook(UserDict):
    
    def add_record(self, record):
        self.data[record.name.value] = record
    
    def delete(self, name):
        if name in self.data:
            del self.data[name]
    
    def find(self, name):
        return self.data.get(name, None)

    # Method for showing upcoming birthdays with congratulation dates
    def get_upcoming_birthday(self):
        upcoming_birthdays = []
        today = datetime.now().date()
        
        for record in self.data.values():
            if record.birthday:
                # cheking if birthday is set
                birthday_date = datetime.strptime(record.birthday.value, '%d.%m.%Y').date()
                
                # seting birthday date to this year
                birthday_this_year = birthday_date.replace(year=today.year)
                
                # if birthday this year is before today, set it to next year
                if birthday_this_year < today:
                    birthday_this_year = birthday_date.replace(year=today.year + 1)
                
                # checking if birthday is within the next 7 days
                if (birthday_this_year - today).days <= 7:
                    # seting congratulation date
                    congratulation_date = birthday_this_year
                    
                    # if birthday is on weekend, set congratulation date to next Monday
                    if birthday_this_year.weekday() == 5:  
                        congratulation_date = birthday_this_year + timedelta(days=2)  
                    elif birthday_this_year.weekday() == 6:  
                        congratulation_date = birthday_this_year + timedelta(days=1)  
                    
                    upcoming_birthdays.append((record.name.value, congratulation_date.strftime('%d.%m.%Y')))
        
        return upcoming_birthdays

    def __str__(self):
        return '\n'.join(str(record) for record in self.data.values())


class Handler(ABC):
    @abstractmethod
    def show_contacts(self, book):
        pass
    @abstractmethod
    def show_phone(self, args, book):
        pass
    @abstractmethod
    def show_birthday(self, args, book):
        pass
    @abstractmethod
    def birthdays(self, book):
        pass


class ContactHandler(Handler):
    def __init__(self, address_book):
        self.address_book = address_book


    def show_phone(self ,args, book):
        name = args[0]
        record = book.find(name)
        if record is None:
            raise KeyError(f'No contact found with name {name}')
        phones = ', '.join(str(phone) for phone in record.phones)
        return f'Phone numbers for {name}: {phones}' if phones else f'No phone numbers found for {name}'
    

    def show_contacts(self, book):
        if not book.data:
            return 'No contacts found.'
        return str(book)
    

    def show_birthday(self, args, book):
        name = args[0]
        record = book.find(name)
        if record is None:
            raise KeyError(f'No contact found with name {name}')
        if record.birthday:
            return f'Birthday for {name}: {record.birthday.value}'
        else:
            return f'No birthday found for {name}'
        

    def birthdays(self, book):
        upcoming_birthdays = book.get_upcoming_birthday()
        if not upcoming_birthdays:
            return 'No upcoming birthdays found.'
        result = "Upcoming birthdays:\n"
        for name, date in upcoming_birthdays:
            result += f'{name}: {date}\n'
        return result.strip()


# Function for parsing input
def parse_input(user_input):
    if not user_input.strip():  # checking if input is empty
        return "", []
    cmd, *args = user_input.split()
    cmd = cmd.lower().strip()
    return cmd, args


# Decorator for handling input errors
def input_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs) 
        except IndexError:
            return 'Please give me name and phone number!'
        except KeyError:
            return 'There is no such person in contacts!'
        except ValueError as e:
            return str(e)
    return inner


# Adding contact
@input_error
def add_contacts(args, book):
    name, phone, *_ = args
    record = book.find(name)
    message = 'Contact updated'
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = 'Contact added'
    if phone:
        record.add_phone(phone)
    return message


#Creating serialization for addressbook
def save_data(book, filename='addressbook.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump(book, f)


#Creating deserialization for addressbook
def load_data(filename='addressbook.pkl'):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()        


# Changing contact number from old to new
@input_error
def change_contacts(args, book):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is None:
        raise KeyError(f'No contact found with name {name}')
    record.edit_phone(old_phone, new_phone)
    return f'Phone number for {name} changed from {old_phone} to {new_phone}'


# Showing phone numbers for contact
@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError(f'No contact found with name {name}')
    phones = ', '.join(str(phone) for phone in record.phones)
    return f'Phone numbers for {name}: {phones}' if phones else f'No phone numbers found for {name}'


# Shows all contacts using __str__ method of AddressBook
def show_all_contacts(book):
    if not book.data:
        return 'No contacts found.'
    return str(book)


# Adding birthday for contact
@input_error
def add_birthday(args, book):
    name, birthday = args
    record = book.find(name)
    if record is None:
        raise KeyError(f'No contact found with name {name}')
    record.add_birthday(birthday)
    return f'Birthday for {name} added: {record.birthday.value}'


# Showing birthday for contact
@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError(f'No contact found with name {name}')
    if record.birthday:
        return f'Birthday for {name}: {record.birthday.value}'
    else:
        return f'No birthday found for {name}'


# Shows upcoming birthdays with congratulation dates
@input_error
def birthdays(book):
    upcoming_birthdays = book.get_upcoming_birthday()
    if not upcoming_birthdays:
        return 'No upcoming birthdays found.'
    result = "Upcoming birthdays:\n"
    for name, date in upcoming_birthdays:
        result += f'{name}: {date}\n'
    return result.strip()


def main():
    book = AddressBook()
    handler = ContactHandler(book)
    print('Welcome to assistant bot!')
    book = load_data()
    while True:
        user_input = input('Enter command: ')
        command, args = parse_input(user_input)

        if not command:  # for empty string input
            print('Please enter a command.')
            continue
        if command in ['exit', 'close']:
            print('Goodbye!')
            break
        elif command == 'hello':
            print('How can i help you?')
        elif command == 'add':
            print(add_contacts(args, book))
        elif command == 'all':
            print(f'All contacts:\n{handler.show_contacts(book)}')
        elif command == 'change':
            print(change_contacts(args, book))
        elif command == 'phone':
            print(handler.show_phone(args, book))
        elif command == 'add-birthday':
            print(add_birthday(args, book))
        elif command == 'show-birthday':
            if not args:
                print('Please provide a name to show birthday.')
                continue  
            print(handler.show_birthday(args, book))
        elif command == 'birthdays':
            print(handler.birthdays(book))
        else:
            print('Invalid command!')
        save_data(book)


if __name__ == '__main__':
    main()