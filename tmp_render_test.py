from src.generators.api_generator import APIGenerator

fake_analysis = {
    'api_endpoints': [
        {
            'function_name': 'calculate_bmi',
            'http_method': 'POST',
            'endpoint_path': '/bmi',
            'description': 'Calculate BMI',
            'input_validation': {
                'required_params': [
                    {'name': 'weight', 'type': 'float'},
                    {'name': 'height', 'type': 'float'}
                ]
            },
            'needs_auth': False
        },
        {
            'function_name': 'add_numbers',
            'http_method': 'POST',
            'endpoint_path': '/add',
            'description': 'Add numbers',
            'input_validation': {
                'required_params': [
                    {'name': 'a', 'type': 'float'},
                    {'name': 'b', 'type': 'float'}
                ]
            },
            'needs_auth': False
        }
    ]
}

print('Rendering template...')
api = APIGenerator()
try:
    out = api._generate_main_file(fake_analysis, 'test_project')
    print('Rendered length:', len(out))
except Exception as e:
    print('ERROR:', type(e), e)
