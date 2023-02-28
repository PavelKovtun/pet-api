# PET API

`REST API` for keeping records of pets (dogs and cats) and with the ability to upload a list of pets in `JSON` using
command line.

Stack: `Python`, `Django Rest Framework`, `PostgreSQL`, `Docker Compose`, `Nginx`, `Gunicorn`

## Requirements

- Python 3.10
- Django 4.1.5
- Django Rest Framework 3.14

## API Endpoints

The project uses `API KEY` authentication. All request handlers accept header `X-API-KEY`, the passed `API-KEY` is compared with the reference `API_KEY`, if it matches, the request is processed, otherwise a `401 Unauthorized` error is returned.

Example:

```
GET /pets
X-API-KEY: abcdef12345
```

### POST /pets (сreate a pet)

`request body`

```
{
    "name" : "My Pet",
    "age" : "7",
    "type" : 2
}
```
`response body`

```
{
    "id": "ce7ba7de-2d72-41a9-ac99-38db6a4fca8b",
    "name": "My Pet",
    "age": 7,
    "type": "dog",
    "photos": [],
    "created_at": "2023-02-27T09:01:58"
}
```

### POST /pets/{id}/photo (upload a pet photo)

`request form data`
```
file: binary
```

`response body`

```
{
    "id": "4cb15cbd-243e-427d-bb60-76f591b13cf8",
    "url": "https://address/filename.extension"
}
```

### GET /pets (get list of pets)

`request query parameters`

 ```
 limit: integer (optional, default=20) -> restriction on the number of entries
 offset: integer (optional, default=0) -> shift of entries from the beginning
 has_photos: boolean (optional)

 has_photos: true -> return entries with photos
 has_photos: false -> return entries without photo
 has_photos was not provided -> return all entries
 ```
 
`response body` 

```
{
    "count": 1002,
    "data": [
        {
            "id": "77450512-5093-4bd7-9f27-f6a5db524488",
            "name": "Kellie",
            "age": 8,
            "type": "cat",
            "photos": [
                {
                    "id": "f8ebbda5-b6fb-4e50-bbd4-13c1bac0a135",
                    "image": "https://address/filename.extension"
                },
                {
                    "id": "751f9add-5530-4cdc-8fd7-afeb5d7a9dea",
                    "image": "https://address/filename.extension"
                }
            ],
            "created_at": "2023-02-24T08:25:48"
        },
        {
            "id": "772744d9-a9b8-41a1-8248-8828377e0bf5",
            "name": "James",
            "age": 12,
            "type": "dog",
            "photos": [
                {
                    "id": "d2899b4e-ca28-4d5f-8696-b1c10e4a4ad7",
                    "image": "https://address/filename.extension"
                }
            ],
            "created_at": "2023-02-22T09:43:28"
        }
    ]
}
```

### DELETE /pets (delete pets)

`IDs` for deletion are passed in the `request body`:

```
{
    "ids" : ["433a203f-5480-442b-b599-01060d988d87",
             "587e5358-6407-4fff-9f86-853ce1849ac7",
             "6796fa0d-f405-4363-881d-6d3694a9655c"
    ]
}
```

`response body`

```
{
    "deleted": 2,
    "errors": [
        {
            "id": "587e5358-6407-4fff-9f86-853ce1849ac7",
            "error": "Pet with the matching ID was not found."
        }
    ]
}
```
 
**NOTE: when a pet is deleted, its photos (records in the database and files) are also deleted**


## Local installation
- Clone the repository and go into it
```
git clone https://github.com/PavelKovtun/pet-api
cd pet-api
```
- Create a virtual environment by running the command
```
python -m venv venv
```
- Activate the virtual environment

`Windows`
```
venv\Scripts\activate.bat 
```
`Unix or MacOS`
```
source venv/bin/activate 
```

- Go to the project folder and install all required dependencies:

```
cd pets
pip install -r requirements.txt
```

- In the current directory `pets` rename the file `.env.dev.template` to `.env.dev` and change the variables:
```
SECRET_KEY=please_change_me
API_KEY=API_KEY
API_KEY_HEADER=X-API-KEY
```

You can generate the `SECRET KEY` [there](https://djecrety.ir/).  
`API_KEY_HEADER` is header which is passed in the request for authentication  
`API_KEY` is header value, which used for authentication  

- Create the migrations and run the server locally:

```
python manage.py migrate
python manage.py runserver
```

## Install test data

To install the test pet data use fixtures:

`pet_types.json` - pet types: cat and dog  
`pets_test_data.json` - 1000 demo pets (without photos)

```
 python manage.py loaddata pets_module/fixtures/pet_types.json --app pets_module.PetType
 python manage.py loaddata pets_module/fixtures/pets_test_data.json --app pets_module.Pet
```

## Tests

This project have a DRF tests. Use the command:

```
python manage.py test

----------------------------------------------------------------------
Ran 23 tests in 0.271s

OK
```

## Deployment Guide to VPS/VDS server

- Install Docker and Docker Compose to your server, use [this](https://docs.docker.com/engine/install/ubuntu/) instruction 
- Clone the repository by enter the command 
```
git clone https://github.com/PavelKovtun/pet-api
```
- Rename the file `.env.db.template` to `.env.db` and change the variables:
```
POSTGRES_USER=POSTGRES_USER
POSTGRES_PASSWORD=POSTGRES_PASSWORD
POSTGRES_DB=POSTGRES_DB
```
To your future access data to the postgres database, which will be created to work within the project.  
- Rename the file `.env.template` to `.env` and change the variables:
```
SECRET_KEY=SECRET_KEY
DJANGO_ALLOWED_HOSTS=ALLOWED_HOSTS
SQL_DATABASE=SQL_DATABASE
SQL_USER=SQL_USER
SQL_PASSWORD=SQL_PASSWORD
API_KEY=API_KEY
API_KEY_HEADER=X-API-KEY
SERVER_ADDRESS=SERVER_ADDRESS
```
You can generate the `SECRET KEY` [there](https://djecrety.ir/).   
`DJANGO_ALLOWED_HOSTS` - a list of strings representing the host/domain names that this Django site can serve, for example `localhost 127.0.0.1`  
`SQL_DATABASE`, `SQL_USER`, `SQL_PASSWORD` - the same as in `.env.db` file  
`API_KEY`, `API_KEY_HEADER` - key and header for authentication.  
`SERVER_ADDRESS` - the server address where django will be host (`http://127.0.0.1:1337` if you are using `docker-compose` locally)  

- Now you can deploy it to docker:

```
docker-compose up -d --build
```

## CLI (client.py)

It is possible to dump pets from the command line to stdout in `JSON` format.

```
usage: client.py [-h] [has_photos]

The program-client to get pets from the command line to stdout in json format.

positional arguments:
  has_photos  Boolean value to filter pets with/without photos.
```

Upload format (different from `API` response):

```
{
    "pets": [
        {
            "id": "433a203f-5480-442b-b599-01060d988d87",
            "name": "boy",
            "age": 7,
            "type": "dog",
            "photos": ["https://address/filename.extension"],
            "created_at": "2023-02-27T10:33:47"
        },
        {
            "id": "6796fa0d-f405-4363-881d-6d3694a9655c",
            "name": "girl",
            "age": 3,
            "type": "cat",
            "photos": ["https://address/filename.extension",
                       "https://address/filename.extension"
            ],
            "created_at": "2023-02-27T22:39:58"
        },
    ]
}
```

Also you can upload data from this client to the file:

```
python client.py > data.json
```

**NOTE!**
The client uses `SERVER_ADDRESS`, `API_KEY`, `API_KEY_HEADER` environment variables in the `.env` file to connect the server, so you need to create the `.env` file locally near to the `client.py` file.

Rename the file `.env.template` to `.env` and change the variables:
```
API_KEY=API_KEY
API_KEY_HEADER=X-API-KEY
SERVER_ADDRESS=SERVER_ADDRESS
```
to

```
API_KEY=YOUR_SERVER_API_KEY
API_KEY_HEADER=YOUR_SERVER_API-KEY-HEADER
SERVER_ADDRESS=YOUR_SERVER_ADDRESS
```

If you use the local `Django` server set the `SERVER_ADDRESS` value to `http://127.0.0.1:8000`.
