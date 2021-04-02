from hypothesis import settings

# set up profiles
settings.register_profile('default', deadline=500)
settings.register_profile('large', max_examples=5000)
settings.register_profile('fast', max_examples=10)
settings.load_profile('default')
