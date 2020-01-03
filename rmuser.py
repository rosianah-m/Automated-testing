#import azure.cosmos.documents as documents
#mport azure.cosmos.cosmos_client as cosmos_client
#import azure.cosmos.errors as errors

def find_database(client, id):
        print('1. Query for Database')

        databases = list(client.QueryDatabases({
            "query": "SELECT * FROM r WHERE r.id=@id",
            "parameters": [
                { "name":"@id", "value": id }
            ]
        }))

        if len(databases) > 0:
            print('Database with id \'{0}\' was found'.format(id))
        else:
            print('No database with id \'{0}\' was found'. format(id))