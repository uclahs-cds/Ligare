"""
This type stub file was generated by pyright.
"""

from saml2 import SamlBase

"""The PasswordProtectedTransport class is applicable when a principal
authenticates to an authentication authority through the presentation of a
password over a protected session."""
NAMESPACE = ...
class PhysicalVerification(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:PhysicalVerification element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, credential_level=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def physical_verification_from_string(xml_string): # -> None:
    ...

class Generation(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:Generation element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, mechanism=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def generation_from_string(xml_string): # -> None:
    ...

class NymType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:nymType element"""
    c_tag = ...
    c_namespace = ...
    c_value_type = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def nym_type__from_string(xml_string): # -> None:
    ...

class GoverningAgreementRefType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:GoverningAgreementRefType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, governing_agreement_ref=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def governing_agreement_ref_type__from_string(xml_string): # -> None:
    ...

class KeySharingType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:KeySharingType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, sharing=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def key_sharing_type__from_string(xml_string): # -> None:
    ...

class RestrictedLengthType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:RestrictedLengthType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, min=..., max=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def restricted_length_type__from_string(xml_string): # -> None:
    ...

class AlphabetType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:AlphabetType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, required_chars=..., excluded_chars=..., case=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def alphabet_type__from_string(xml_string): # -> None:
    ...

class DeviceTypeType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:DeviceTypeType element"""
    c_tag = ...
    c_namespace = ...
    c_value_type = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def device_type_type__from_string(xml_string): # -> None:
    ...

class BooleanType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:booleanType element"""
    c_tag = ...
    c_namespace = ...
    c_value_type = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def boolean_type__from_string(xml_string): # -> None:
    ...

class TimeSyncTokenType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:TimeSyncTokenType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, device_type=..., seed_length=..., device_in_hand=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def time_sync_token_type__from_string(xml_string): # -> None:
    ...

class ActivationLimitDurationType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ActivationLimitDurationType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, duration=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def activation_limit_duration_type__from_string(xml_string): # -> None:
    ...

class ActivationLimitUsagesType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ActivationLimitUsagesType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, number=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def activation_limit_usages_type__from_string(xml_string): # -> None:
    ...

class ActivationLimitSessionType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ActivationLimitSessionType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def activation_limit_session_type__from_string(xml_string): # -> None:
    ...

class LengthType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:LengthType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, min=..., max=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def length_type__from_string(xml_string): # -> None:
    ...

class MediumType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:mediumType element"""
    c_tag = ...
    c_namespace = ...
    c_value_type = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def medium_type__from_string(xml_string): # -> None:
    ...

class KeyStorageType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:KeyStorageType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, medium=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def key_storage_type__from_string(xml_string): # -> None:
    ...

class ExtensionType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ExtensionType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def extension_type__from_string(xml_string): # -> None:
    ...

class KeySharing(KeySharingType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:KeySharing element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def key_sharing_from_string(xml_string): # -> None:
    ...

class KeyStorage(KeyStorageType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:KeyStorage element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def key_storage_from_string(xml_string): # -> None:
    ...

class TimeSyncToken(TimeSyncTokenType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:TimeSyncToken element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def time_sync_token_from_string(xml_string): # -> None:
    ...

class Length(LengthType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:Length element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def length_from_string(xml_string): # -> None:
    ...

class GoverningAgreementRef(GoverningAgreementRefType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:GoverningAgreementRef element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def governing_agreement_ref_from_string(xml_string): # -> None:
    ...

class GoverningAgreementsType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:GoverningAgreementsType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, governing_agreement_ref=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def governing_agreements_type__from_string(xml_string): # -> None:
    ...

class RestrictedPasswordType_Length(RestrictedLengthType_):
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def restricted_password_type__length_from_string(xml_string): # -> None:
    ...

class Alphabet(AlphabetType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:Alphabet element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def alphabet_from_string(xml_string): # -> None:
    ...

class ActivationLimitDuration(ActivationLimitDurationType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ActivationLimitDuration element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def activation_limit_duration_from_string(xml_string): # -> None:
    ...

class ActivationLimitUsages(ActivationLimitUsagesType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ActivationLimitUsages element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def activation_limit_usages_from_string(xml_string): # -> None:
    ...

class ActivationLimitSession(ActivationLimitSessionType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ActivationLimitSession element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def activation_limit_session_from_string(xml_string): # -> None:
    ...

class Extension(ExtensionType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:Extension element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def extension_from_string(xml_string): # -> None:
    ...

class SharedSecretChallengeResponseType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:SharedSecretChallengeResponseType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, extension=..., method=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def shared_secret_challenge_response_type__from_string(xml_string): # -> None:
    ...

class PublicKeyType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:PublicKeyType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, extension=..., key_validation=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def public_key_type__from_string(xml_string): # -> None:
    ...

class GoverningAgreements(GoverningAgreementsType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:GoverningAgreements element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def governing_agreements_from_string(xml_string): # -> None:
    ...

class PasswordType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:PasswordType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, length=..., alphabet=..., generation=..., extension=..., external_verification=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def password_type__from_string(xml_string): # -> None:
    ...

class RestrictedPasswordType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:RestrictedPasswordType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, length=..., generation=..., extension=..., external_verification=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def restricted_password_type__from_string(xml_string): # -> None:
    ...

class TokenType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:TokenType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, time_sync_token=..., extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def token_type__from_string(xml_string): # -> None:
    ...

class ActivationLimitType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ActivationLimitType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, activation_limit_duration=..., activation_limit_usages=..., activation_limit_session=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def activation_limit_type__from_string(xml_string): # -> None:
    ...

class ExtensionOnlyType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ExtensionOnlyType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def extension_only_type__from_string(xml_string): # -> None:
    ...

class WrittenConsent(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:WrittenConsent element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def written_consent_from_string(xml_string): # -> None:
    ...

class SubscriberLineNumber(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:SubscriberLineNumber element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def subscriber_line_number_from_string(xml_string): # -> None:
    ...

class UserSuffix(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:UserSuffix element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def user_suffix_from_string(xml_string): # -> None:
    ...

class Password(PasswordType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:Password element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def password_from_string(xml_string): # -> None:
    ...

class Token(TokenType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:Token element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def token_from_string(xml_string): # -> None:
    ...

class Smartcard(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:Smartcard element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def smartcard_from_string(xml_string): # -> None:
    ...

class ActivationLimit(ActivationLimitType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ActivationLimit element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def activation_limit_from_string(xml_string): # -> None:
    ...

class PreviousSession(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:PreviousSession element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def previous_session_from_string(xml_string): # -> None:
    ...

class ResumeSession(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ResumeSession element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def resume_session_from_string(xml_string): # -> None:
    ...

class ZeroKnowledge(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ZeroKnowledge element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def zero_knowledge_from_string(xml_string): # -> None:
    ...

class SharedSecretChallengeResponse(SharedSecretChallengeResponseType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:SharedSecretChallengeResponse element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def shared_secret_challenge_response_from_string(xml_string): # -> None:
    ...

class DigSig(PublicKeyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:DigSig element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def dig_sig_from_string(xml_string): # -> None:
    ...

class AsymmetricDecryption(PublicKeyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:AsymmetricDecryption element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def asymmetric_decryption_from_string(xml_string): # -> None:
    ...

class AsymmetricKeyAgreement(PublicKeyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:AsymmetricKeyAgreement element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def asymmetric_key_agreement_from_string(xml_string): # -> None:
    ...

class IPAddress(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:IPAddress element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def ip_address_from_string(xml_string): # -> None:
    ...

class SharedSecretDynamicPlaintext(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:SharedSecretDynamicPlaintext element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def shared_secret_dynamic_plaintext_from_string(xml_string): # -> None:
    ...

class HTTP(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:HTTP element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def http_from_string(xml_string): # -> None:
    ...

class IPSec(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:IPSec element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def ip_sec_from_string(xml_string): # -> None:
    ...

class WTLS(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:WTLS element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def wtls_from_string(xml_string): # -> None:
    ...

class MobileNetworkNoEncryption(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:MobileNetworkNoEncryption element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def mobile_network_no_encryption_from_string(xml_string): # -> None:
    ...

class MobileNetworkRadioEncryption(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:MobileNetworkRadioEncryption element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def mobile_network_radio_encryption_from_string(xml_string): # -> None:
    ...

class MobileNetworkEndToEndEncryption(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:MobileNetworkEndToEndEncryption element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def mobile_network_end_to_end_encryption_from_string(xml_string): # -> None:
    ...

class SSL(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:SSL element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def ssl_from_string(xml_string): # -> None:
    ...

class PSTN(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:PSTN element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def pstn_from_string(xml_string): # -> None:
    ...

class ISDN(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ISDN element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def isdn_from_string(xml_string): # -> None:
    ...

class ADSL(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ADSL element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def adsl_from_string(xml_string): # -> None:
    ...

class SwitchAudit(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:SwitchAudit element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def switch_audit_from_string(xml_string): # -> None:
    ...

class DeactivationCallCenter(ExtensionOnlyType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:DeactivationCallCenter element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def deactivation_call_center_from_string(xml_string): # -> None:
    ...

class IdentificationType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:IdentificationType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, physical_verification=..., written_consent=..., governing_agreements=..., extension=..., nym=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def identification_type__from_string(xml_string): # -> None:
    ...

class RestrictedPassword(RestrictedPasswordType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:RestrictedPassword element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def restricted_password_from_string(xml_string): # -> None:
    ...

class ActivationPinType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ActivationPinType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, length=..., alphabet=..., generation=..., activation_limit=..., extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def activation_pin_type__from_string(xml_string): # -> None:
    ...

class SecurityAuditType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:SecurityAuditType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, switch_audit=..., extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def security_audit_type__from_string(xml_string): # -> None:
    ...

class AuthenticatorBaseType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:AuthenticatorBaseType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, restricted_password=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def authenticator_base_type__from_string(xml_string): # -> None:
    ...

class AuthenticatorTransportProtocolType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:AuthenticatorTransportProtocolType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, ssl=..., mobile_network_radio_encryption=..., mobile_network_end_to_end_encryption=..., wtls=..., ip_sec=..., extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def authenticator_transport_protocol_type__from_string(xml_string): # -> None:
    ...

class Identification(IdentificationType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:Identification element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def identification_from_string(xml_string): # -> None:
    ...

class ActivationPin(ActivationPinType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ActivationPin element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def activation_pin_from_string(xml_string): # -> None:
    ...

class Authenticator(AuthenticatorBaseType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:Authenticator element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def authenticator_from_string(xml_string): # -> None:
    ...

class AuthenticatorTransportProtocol(AuthenticatorTransportProtocolType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:AuthenticatorTransportProtocol element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def authenticator_transport_protocol_from_string(xml_string): # -> None:
    ...

class SecurityAudit(SecurityAuditType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:SecurityAudit element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def security_audit_from_string(xml_string): # -> None:
    ...

class OperationalProtectionType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:OperationalProtectionType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, security_audit=..., deactivation_call_center=..., extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def operational_protection_type__from_string(xml_string): # -> None:
    ...

class PrincipalAuthenticationMechanismType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:PrincipalAuthenticationMechanismType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, password=..., restricted_password=..., token=..., smartcard=..., activation_pin=..., extension=..., preauth=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def principal_authentication_mechanism_type__from_string(xml_string): # -> None:
    ...

class KeyActivationType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:KeyActivationType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, activation_pin=..., extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def key_activation_type__from_string(xml_string): # -> None:
    ...

class KeyActivation(KeyActivationType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:KeyActivation element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def key_activation_from_string(xml_string): # -> None:
    ...

class PrincipalAuthenticationMechanism(PrincipalAuthenticationMechanismType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:PrincipalAuthenticationMechanism element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def principal_authentication_mechanism_from_string(xml_string): # -> None:
    ...

class OperationalProtection(OperationalProtectionType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:OperationalProtection element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def operational_protection_from_string(xml_string): # -> None:
    ...

class PrivateKeyProtectionType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:PrivateKeyProtectionType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, key_activation=..., key_storage=..., key_sharing=..., extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def private_key_protection_type__from_string(xml_string): # -> None:
    ...

class SecretKeyProtectionType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:SecretKeyProtectionType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, key_activation=..., key_storage=..., extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def secret_key_protection_type__from_string(xml_string): # -> None:
    ...

class AuthnMethodBaseType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:AuthnMethodBaseType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, principal_authentication_mechanism=..., authenticator=..., authenticator_transport_protocol=..., extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def authn_method_base_type__from_string(xml_string): # -> None:
    ...

class SecretKeyProtection(SecretKeyProtectionType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:SecretKeyProtection element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def secret_key_protection_from_string(xml_string): # -> None:
    ...

class PrivateKeyProtection(PrivateKeyProtectionType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:PrivateKeyProtection element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def private_key_protection_from_string(xml_string): # -> None:
    ...

class AuthnMethod(AuthnMethodBaseType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:AuthnMethod element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def authn_method_from_string(xml_string): # -> None:
    ...

class TechnicalProtectionBaseType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:TechnicalProtectionBaseType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, private_key_protection=..., secret_key_protection=..., extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def technical_protection_base_type__from_string(xml_string): # -> None:
    ...

class TechnicalProtection(TechnicalProtectionBaseType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:TechnicalProtection element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def technical_protection_from_string(xml_string): # -> None:
    ...

class AuthnContextDeclarationBaseType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:AuthnContextDeclarationBaseType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, identification=..., technical_protection=..., operational_protection=..., authn_method=..., governing_agreements=..., extension=..., id=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def authn_context_declaration_base_type__from_string(xml_string): # -> None:
    ...

class AuthenticationContextDeclaration(AuthnContextDeclarationBaseType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:AuthenticationContextDeclaration element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def authentication_context_declaration_from_string(xml_string): # -> None:
    ...

class ComplexAuthenticatorType_(SamlBase):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ComplexAuthenticatorType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, previous_session=..., resume_session=..., dig_sig=..., password=..., restricted_password=..., zero_knowledge=..., shared_secret_challenge_response=..., shared_secret_dynamic_plaintext=..., ip_address=..., asymmetric_decryption=..., asymmetric_key_agreement=..., subscriber_line_number=..., user_suffix=..., complex_authenticator=..., extension=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def complex_authenticator_type__from_string(xml_string): # -> None:
    ...

class ComplexAuthenticator(ComplexAuthenticatorType_):
    """The urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport:ComplexAuthenticator element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def complex_authenticator_from_string(xml_string): # -> None:
    ...

ELEMENT_FROM_STRING = ...
ELEMENT_BY_TAG = ...
def factory(tag, **kwargs):
    ...
