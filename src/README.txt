Build instructions:
1. go into assignment folder
2. execute:
	docker-compose build
	docker-compose up -d
3. check if container exists - run: docker ps

Run app:
1. go into assignment folder
2. execute:
	docker exec -it assignment sh
	FLASK_APP=app.py flask run -h 0.0.0 -p 5000

Test app:
1. go to localhost:5003
2. in section POST request select file named 'example_file.txt' and click Send POST
3. your response shoud look like this:
{"the group": 20, "was released": 13, "released on": 13, "on the": 12, "in the": 9, "of the": 8, "the album": 8, "the single": 8, "and offset": 7, "at number": 7}
4. go back to localhost:5003
5. in section GET request input into field "Migos" and click send GET
6. you should get this response:
{"the group": 20, "was released": 13, "released on": 13, "on the": 12, "in the": 9, "migos released": 8, "of the": 8, "the album": 8, "the single": 8, "and offset": 7}

Usage:
In POST request section you can put enter any .txt file and on click Send POST, you will
get top 10 most frequently occurring pairs of successive words, in that file.

In GET request section you can enter any english wikipedia name and after you will get
 top 10 most frequently occurring pairs of successive words, in that article.