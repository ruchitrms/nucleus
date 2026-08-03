Date: JULY 24

# Week 1
# Day - 1
- Started the project and created the folder structure. 
learned few things while creating the base project with the folder structure. The first thing I go to know is that the reuirements.txt structure, we can have 2 requirements.txt which is base and dev and base is which holds the productiuon level libs and dev is somehting which needs to be installed locally for dev that includes testing libs etc. Good to know this pattern exist never knew we can have this structure as well.
Second thing about the folder structure, got to know there are 3 folder structure layer first, domain first and clean architecture, I wanted to have this backend service as a micro-service but later got to know that each service in this e-commerce can be or should be as a micro-service so for now as a solo project i went ahead with layer first in the refactor phase I might try to have a micro service, can you explain what is monolith do we call this micro-service pattern monolith? but yes this is what I got to lern today

# Day - 2 
- So started with understanding the refresh token why do we need it? and how do we use it. Didn;t the knew ever why access token is short lived eg if it is ever stolen then the attacker have the access of it for lifetime. Created the docker-compose file from scrath line by line by knowing what every attribute means. created config file so that we can use this file anywhere where we need to fetch values from env variables. also got to know about the sessionmake and async session maker as a android dev I understodd that is we use sessionmaker to open the db connection and do the transaction it will block the main thread alteast thats what we used to call in android so hence using async session maker makes sense.

# Day - 3
- Created the models of users and refresh token, understood the Mapped[Str] defninig method and that too this is not nullable and if we need to create nullable then it is | None and we can assign default value, understodd the index= true usage why do we add this the actually find that value using the index from multiple rows.the next important thing is the albemic the migration tool which is used in industry how it helps o reduce the manula work for migration the table to sync postgres sql db

# Day - 4
- Okay so I understood the repository pattern I think this is similar to android repository pattern which take cares of getting the data from the source, so in android we used to have viewmodel which used to call the repository and its hish job of getting the data the viewmodel is not aware from wherer the data is coming. So here the repo is the only way from where the db data is updated. Services -> Repo. Routes -> Services so basically Routes -> Services -> Repo. Completed my week 1 tasks and understodd how the flow works for sign up and login and how hashing works and how it stored the hashing created mermaid live diagram for better understanding. 

Week 1 - o/p - Net result: You have a working auth system (signup, login, hashing, tokens) built on a deliberately chosen folder structure, with migrations set up via Alembic — and, more importantly, you can explain why each piece works the way it does, not just that it runs. That's exactly the checkpoint Week 1 was meant to hit.

# Day - 5
- Started with week 2 plan- created a centrailized exception handler where that class extends the base exception class so that any exceptionn can be parsed and created different classes which extends this base class so that exeception can be parsed as we move ahead will add more class for handling other execeptions as well, like one source of truth for execption so going forward we will have only place to lookk for.