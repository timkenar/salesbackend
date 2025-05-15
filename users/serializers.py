from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name') # Add other fields as needed

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name') # Add other fields as needed
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class UsernameEmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Override the default username field to accept either username or email
    username_field = 'username' # This is just a label, the validation handles both

    def validate(self, attrs):
        # The 'username' field in the request can be either username or email
        username_or_email = attrs.get('username')
        password = attrs.get('password')

        if not username_or_email or not password:
             raise serializers.ValidationError('Must include "username or email" and "password".')

        user = None

        # Try authenticating with username first
        user = authenticate(request=self.context.get('request'),
                            username=username_or_email,
                            password=password)

        # If authentication failed, try authenticating with email
        if user is None:
            try:
                # Find user by email
                user_by_email = User.objects.get(email=username_or_email)
                # Authenticate using the found user's username
                user = authenticate(request=self.context.get('request'),
                                    username=user_by_email.username,
                                    password=password)
            except User.DoesNotExist:
                # User not found by email
                pass # user remains None

        if user is None:
            raise serializers.ValidationError('No active account found with the given credentials')

        # If user is found and active, proceed to get tokens
        if not user.is_active:
             raise serializers.ValidationError('This account is inactive.')

        # Get the default token data
        data = super().validate(attrs)

        # Optionally update last login time
        update_last_login(None, user)

        # You can add custom data to the response if needed
        # data['user_id'] = user.id
        # data['username'] = user.username

        return data