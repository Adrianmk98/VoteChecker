This code requires Google API,as well as reddit API. The encription exists in order to encrypt the autoupdater.json which houses the data directly. It will turn the json into json.enc along with a secret key which is required for the code to work.
The code takes updates the player.txt from the database of players, and checks how they voted on the linked thread
![image](https://github.com/user-attachments/assets/1bac614b-7f42-451e-8785-fea5b1df669f)

it keeps each players voting results, and if they comment again to change their vote it will track that too. It also keeps a list of who has not voted or who had voted at the time but is no longer an MP

![image](https://github.com/user-attachments/assets/b59ff09b-9f91-455a-87a3-200d778758e7)


