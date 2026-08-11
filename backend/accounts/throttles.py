from rest_framework.throttling import AnonRateThrottle


class RegistrationThrottle(AnonRateThrottle):
    rate = "10/hour"


class LoginThrottle(AnonRateThrottle):
    rate = "30/hour"
