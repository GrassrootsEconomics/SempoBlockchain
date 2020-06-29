import pytest
from functools import partial
from faker.providers import phone_number
from faker import Faker

from helpers.factories import UserFactory, UssdSessionFactory, OrganisationFactory, TokenFactory
from helpers.ussd_utils import fake_transfer_mapping
from server import db
from server.utils.ussd.kenya_ussd_state_machine import KenyaUssdStateMachine
from server.models.user import User
from server.models.transfer_usage import TransferUsage
import config

fake = Faker()
fake.add_provider(phone_number)
# why do i get dupes if i put it directly on standard_user...?
phone = partial(fake.msisdn)

standard_user = partial(UserFactory, pin_hash=User.salt_hash_secret('0000'), failed_pin_attempts=0)

initial_language_selection_state = partial(UssdSessionFactory, state="initial_language_selection")
start_state = partial(UssdSessionFactory, state="start")
account_management_state = partial(UssdSessionFactory, state="account_management")
user_profile_state = partial(UssdSessionFactory, state="user_profile")
my_business_state = partial(UssdSessionFactory, state="my_business")
choose_language_state = partial(UssdSessionFactory, state="choose_language")
directory_listing_state = partial(UssdSessionFactory, state="directory_listing")
directory_listing_other_state = partial(UssdSessionFactory, state="directory_listing_other")
help_state = partial(UssdSessionFactory, state="help")
exit_invalid_menu_option_state = partial(UssdSessionFactory, state="exit_invalid_menu_option")
exit_use_exchange_menu_state = partial(UssdSessionFactory, state="exit_use_exchange_menu")
exit_invalid_recipient_state = partial(UssdSessionFactory, state="exit_invalid_recipient")
exit_invalid_token_agent_state = partial(UssdSessionFactory, state="exit_invalid_token_agent")
complete_state = partial(UssdSessionFactory, state="complete")
exit_successful_send_token_state = partial(UssdSessionFactory, state="exit_successful_send_token")
exit_invalid_input_state =  partial(UssdSessionFactory, state="exit_invalid_input")


@pytest.mark.parametrize("session_factory, user_factory, user_input, expected",
 [
     # initial_language_selection transitions tests
     (initial_language_selection_state, standard_user, "3", "help"),
     (initial_language_selection_state, standard_user, "5", "exit_invalid_menu_option"),
     (initial_language_selection_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # start state transition tests
     (start_state, standard_user, "1", "send_enter_recipient"),
     (start_state, standard_user, "2", "account_management"),
     (start_state, standard_user, "3", "directory_listing"),
     (start_state, standard_user, "4", "exchange_token"),
     (start_state, standard_user, "5", "help"),
     (start_state, standard_user, "6", "exit_invalid_menu_option"),
     (start_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # account_management state tests
     (account_management_state, standard_user, "1", "user_profile"),
     (account_management_state, standard_user, "2", "choose_language"),
     (account_management_state, standard_user, "3", "mini_statement_inquiry_pin_authorization"),
     (account_management_state, standard_user, "4", "current_pin"),
     (account_management_state, standard_user, "5", "opt_out_of_market_place_pin_authorization"),
     (account_management_state, standard_user, "6", "exit_invalid_menu_option"),
     (account_management_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # user_profile state tests
     (user_profile_state, standard_user, "1", "first_name_entry"),
     (user_profile_state, standard_user, "2", "gender_entry"),
     (user_profile_state, standard_user, "3", "location_entry"),
     (user_profile_state, standard_user, "4", "change_my_business_prompt"),
     (user_profile_state, standard_user, "5", "view_profile_pin_authorization"),
     (user_profile_state, standard_user, "6", "exit_invalid_menu_option"),
     (user_profile_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # directory listing state tests
     (directory_listing_state, standard_user, "9", "directory_listing_other"),
     (directory_listing_state, standard_user, "1", "complete"),
     (directory_listing_state, standard_user, "10", "exit_invalid_menu_option"),
     (directory_listing_state, standard_user, "11", "exit_invalid_menu_option"),
     (directory_listing_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # directory listing other state tests
     (directory_listing_other_state, standard_user, "1", "complete"),
     (directory_listing_other_state, standard_user, "9", "directory_listing_other"),
     (directory_listing_other_state, standard_user, "10", "directory_listing_other"),
     (directory_listing_other_state, standard_user, "11", "exit_invalid_menu_option"),
     (directory_listing_other_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # choose_language state tests
     (choose_language_state, standard_user, "5", "exit_invalid_menu_option"),
     (choose_language_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # back options
     (help_state, standard_user, "9", "exit"),
     (exit_invalid_menu_option_state, standard_user, "00", "start"),
     (exit_invalid_menu_option_state, standard_user, "99", "exit"),
     (exit_use_exchange_menu_state, standard_user, "00", "exchange_token"),
     (exit_use_exchange_menu_state, standard_user, "99", "exit"),
     (exit_invalid_recipient_state, standard_user, "00", "send_enter_recipient"),
     (exit_invalid_recipient_state, standard_user, "99", "exit"),
     (exit_invalid_token_agent_state, standard_user, "00", "exchange_token_agent_number_entry"),
     (complete_state, standard_user, "00", "start"),
     (complete_state, standard_user, "99", "exit"),
     (exit_successful_send_token_state, standard_user, "00", "start"),
     (exit_successful_send_token_state, standard_user, "99", "exit"),
     (exit_invalid_input_state, standard_user, "00", "start"),
     (exit_invalid_input_state, standard_user, "99", "exit")
 ])
def test_kenya_state_machine(test_client, init_database, user_factory, session_factory, user_input, expected):
    token = TokenFactory(name='Sarafu', symbol='SARAFU')
    from flask import g
    organisation = OrganisationFactory(country_code=config.DEFAULT_COUNTRY, token=token)
    g.active_organisation = organisation

    session = session_factory()
    session.session_data = {
        'transfer_usage_mapping': fake_transfer_mapping(10),
        'usage_menu': 1,
        'usage_index_stack': [0, 8],
        'recipient_phone': phone()
    }
    user = user_factory()
    user.default_organisation = organisation
    user.phone = phone()
    db.session.commit()
    state_machine = KenyaUssdStateMachine(session, user)

    state_machine.feed_char(user_input)
    assert state_machine.state == expected


@pytest.mark.parametrize("session_factory, user_input, language", [
    (initial_language_selection_state, "1", "en"),
    (initial_language_selection_state, "2", "sw"),
])
def test_change_language_initial(mocker, test_client, init_database, session_factory, user_input, language):
    session = session_factory()
    user = standard_user()
    assert user.preferred_language is None

    state_machine = KenyaUssdStateMachine(session, user)

    state_machine.feed_char(user_input)
    assert state_machine.state == "initial_pin_entry"
    assert user.preferred_language == language

@pytest.mark.parametrize("session_factory, user_input, language", [
    (choose_language_state, "1", "en"),
    (choose_language_state, "2", "sw"),
])
def test_change_language(mocker, test_client, init_database, session_factory, user_input, language):
    session = session_factory()
    user = standard_user()
    user.phone = phone()
    assert user.preferred_language is None

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.send_sms = mocker.MagicMock()

    state_machine.feed_char(user_input)
    assert state_machine.state == "complete"
    assert user.preferred_language == language
    state_machine.send_sms.assert_called_with(user.phone, "language_change_sms")


def test_opt_out_of_marketplace(mocker, test_client, init_database):
    session = UssdSessionFactory(state="opt_out_of_market_place_pin_authorization")
    user = standard_user()
    user.phone = phone()
    assert next(filter(lambda x: x.name == 'market_enabled', user.custom_attributes), None) is None
    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.send_sms = mocker.MagicMock()

    state_machine.feed_char("0000")
    assert state_machine.state == "complete"
    assert user.is_market_enabled == False
    state_machine.send_sms.assert_called_with(user.phone, "opt_out_of_market_place_sms")


def test_save_directory_info(mocker, test_client, init_database):
    session = UssdSessionFactory(state="change_my_business_prompt")
    user = standard_user()
    user.phone = phone()
    assert next(filter(lambda x: x.name == 'bio', user.custom_attributes), None) is None
    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.send_sms = mocker.MagicMock()

    state_machine.feed_char("My Bio")
    session.session_data = {
        'bio': "My Bio"
    }
    assert state_machine.state == "profile_info_change_pin_authorization"
    state_machine.feed_char("0000")
    bio = next(filter(lambda x: x.name == 'bio', user.custom_attributes), None)
    assert bio.value == "My Bio"


def test_balance_inquiry(mocker, test_client, init_database):
    session = UssdSessionFactory(state="balance_inquiry_pin_authorization")
    user = standard_user()
    user.phone = phone()

    state_machine = KenyaUssdStateMachine(session, user)
    inquire_balance = mocker.MagicMock()
    mocker.patch('server.ussd_tasker.inquire_balance', inquire_balance)

    state_machine.feed_char('0000')
    assert state_machine.state == 'complete'
    inquire_balance.assert_called_with(user)


def test_send_directory_listing(mocker, test_client, init_database):
    session = UssdSessionFactory(state="directory_listing")
    session.session_data = {'transfer_usage_mapping': fake_transfer_mapping(6), 'usage_menu': 0}
    user = standard_user()
    user.phone = phone()
    state_machine = KenyaUssdStateMachine(session, user)
    transfer_usage = TransferUsage.find_or_create("Food")

    send_directory_listing = mocker.MagicMock()
    mocker.patch('server.ussd_tasker.send_directory_listing', send_directory_listing)

    state_machine.feed_char('2')
    assert state_machine.state == 'complete'
    send_directory_listing.assert_called_with(user, transfer_usage)


def test_terms_only_sent_once(mocker, test_client, init_database, mock_sms_apis):
    session = UssdSessionFactory(state="balance_inquiry_pin_authorization")
    user = standard_user()
    user.phone = phone()

    inquire_balance = mocker.MagicMock()
    mocker.patch('server.ussd_tasker.inquire_balance', inquire_balance)

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char('0000')

    db.session.commit()

    messages = mock_sms_apis

    assert len(messages) == 1

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char('0000')

    assert len(messages) == 1
