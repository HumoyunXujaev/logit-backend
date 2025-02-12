from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from drf_spectacular.utils import extend_schema, OpenApiExample

class TelegramAuthScheme(OpenApiAuthenticationExtension):
    target_class = 'users.auth.TelegramAuthBackend'
    name = 'TelegramAuth'
    
    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Telegram WebApp authentication using JWT tokens'
        }

# Common response examples
SERVER_ERROR_RESPONSE = {
    'type': 'object',
    'properties': {
        'detail': {'type': 'string'}
    },
    'example': {'detail': 'Internal server error occurred'}
}

VALIDATION_ERROR_RESPONSE = {
    'type': 'object',
    'properties': {
        'field_name': {
            'type': 'array',
            'items': {'type': 'string'}
        }
    },
    'example': {
        'field_name': ['This field is required.']
    }
}

# Authentication examples
AUTH_SUCCESS_RESPONSE = {
    'type': 'object',
    'properties': {
        'access': {'type': 'string'},
        'refresh': {'type': 'string'},
        'user': {
            'type': 'object',
            'properties': {
                'id': {'type': 'string'},
                'username': {'type': 'string'},
                'role': {'type': 'string'}
            }
        }
    },
    'example': {
        'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
        'user': {
            'id': '123456789',
            'username': 'john_doe',
            'role': 'carrier'
        }
    }
}

# User response examples
USER_PROFILE_RESPONSE = {
    'type': 'object',
    'properties': {
        'telegram_id': {'type': 'string'},
        'username': {'type': 'string'},
        'full_name': {'type': 'string'},
        'role': {'type': 'string'},
        'type': {'type': 'string'},
        'is_verified': {'type': 'boolean'},
        'rating': {'type': 'number'}
    },
    'example': {
        'telegram_id': '123456789',
        'username': 'john_doe',
        'full_name': 'John Doe',
        'role': 'carrier',
        'type': 'individual',
        'is_verified': True,
        'rating': 4.8
    }
}

# Cargo response examples
CARGO_RESPONSE = {
    'type': 'object',
    'properties': {
        'id': {'type': 'integer'},
        'title': {'type': 'string'},
        'description': {'type': 'string'},
        'weight': {'type': 'number'},
        'volume': {'type': 'number'},
        'loading_point': {'type': 'string'},
        'unloading_point': {'type': 'string'},
        'loading_date': {'type': 'string', 'format': 'date'},
        'status': {'type': 'string'},
        'owner': {'$ref': '#/components/schemas/UserProfile'},
        'created_at': {'type': 'string', 'format': 'date-time'}
    },
    'example': {
        'id': 1,
        'title': 'Steel Products',
        'description': 'Steel pipes for construction',
        'weight': 20.5,
        'volume': 40.0,
        'loading_point': 'Tashkent',
        'unloading_point': 'Moscow',
        'loading_date': '2024-02-01',
        'status': 'active',
        'owner': USER_PROFILE_RESPONSE['example'],
        'created_at': '2024-01-20T10:30:00Z'
    }
}

# Vehicle response examples
VEHICLE_RESPONSE = {
    'type': 'object',
    'properties': {
        'id': {'type': 'integer'},
        'registration_number': {'type': 'string'},
        'body_type': {'type': 'string'},
        'capacity': {'type': 'number'},
        'volume': {'type': 'number'},
        'owner': {'$ref': '#/components/schemas/UserProfile'},
        'is_verified': {'type': 'boolean'},
        'documents': {
            'type': 'array',
            'items': {'$ref': '#/components/schemas/VehicleDocument'}
        }
    },
    'example': {
        'id': 1,
        'registration_number': 'AA123BB',
        'body_type': 'tent',
        'capacity': 20.0,
        'volume': 86.0,
        'owner': USER_PROFILE_RESPONSE['example'],
        'is_verified': True,
        'documents': []
    }
}

# Common OpenAPI operation descriptions
OPERATIONS = {
    'list': {
        'summary': 'List objects',
        'description': 'Get a paginated list of objects'
    },
    'create': {
        'summary': 'Create object',
        'description': 'Create a new object'
    },
    'retrieve': {
        'summary': 'Get object',
        'description': 'Get object details by ID'
    },
    'update': {
        'summary': 'Update object',
        'description': 'Update object details'
    },
    'delete': {
        'summary': 'Delete object',
        'description': 'Delete an object'
    }
}

# Common OpenAPI parameters
COMMON_PARAMS = {
    'id': OpenApiExample(
        'ID',
        description='Object ID',
        value=1,
        parameter_only=True
    ),
    'page': OpenApiExample(
        'Page',
        description='Page number',
        value=1,
        parameter_only=True
    ),
    'limit': OpenApiExample(
        'Limit',
        description='Number of results per page',
        value=20,
        parameter_only=True
    )
}

# Common OpenAPI tags
TAGS = {
    'auth': 'Authentication',
    'users': 'Users',
    'cargo': 'Cargo',
    'vehicles': 'Vehicles',
    'core': 'Core'
}