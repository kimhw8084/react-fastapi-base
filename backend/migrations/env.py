from alembic import context

config = context.config
connection = config.attributes.get('connection')
if connection is None:
    raise RuntimeError('Use the Golden migration command; ad-hoc DB URLs are not accepted.')
context.configure(connection=connection, render_as_batch=True)
with context.begin_transaction():
    context.run_migrations()
