import requests, bs4
import sqlite3

db = sqlite3.connect('recipes.db')
cursor = db.cursor()

def parsePrepTime(prepTimeStr):
	token = "time"
	prepTime = 0
	currTime = 0
	for i in prepTimeStr.split(' '):
		if token == "time":
			currTime = int(i)
			token = "unit"
		elif token == "unit":
			if i=='h':
				currTime = currTime*60
			prepTime = prepTime + currTime
			token = "time"
	return prepTime

def inDatabase(table, column, value):
	query = "SELECT * FROM " + table + " WHERE " + column + "=?"
	cursor.execute(query, (value,))
	row = cursor.fetchone()
	if row is None:
		return False
	return True

def getRecipeId(recipe_name):
	query = "SELECT recipe_id FROM recipes WHERE recipe_name='" + recipe_name + "'"
	cursor.execute(query)
	row = cursor.fetchone()
	return int(row[0])

def processRecipe(link, category):
	print(link)
	res = requests.get(link)
	soup = bs4.BeautifulSoup(res.text, 'html.parser')
	
	titleTag = soup.select('h1#recipe-main-content')
	if len(titleTag) > 0:
		title = soup.select('h1#recipe-main-content')[0].string
		title = title.replace("'", "")
	else:
		return
	print(title)

	ingredients = {}
	ingredTags = soup.select('span.recipe-ingred_txt.added')
	for i in ingredTags:
		if i.has_attr('itemprop'):
			ingredients[i['data-id']] = i.string

	timeTag = soup.select('time[itemprop="totalTime"]')
	prepTimeStr = ""
	if len(timeTag) == 0:
		return
	for string in timeTag[0].strings:
		prepTimeStr = prepTimeStr + string

	prepTime = parsePrepTime(prepTimeStr)
	values = (title, prepTime, link, category)

	if not inDatabase('recipes', 'recipe_name', title):
		query = '''INSERT INTO recipes (recipe_name, recipe_preptime, recipe_link, recipe_category)
			VALUES (?, ?, ?, ?)'''
		cursor.execute(query, values)

		recipeId = getRecipeId(title)
		for key in ingredients:
			if not inDatabase('ingredients', 'ingredient_id', key):
				cursor.execute("INSERT INTO ingredients (ingredient_id, ingredient_name) VALUES (?, ?)", (key, ingredients[key]))
			cursor.execute("INSERT INTO recipe_ingredients (ri_recipe_id, ri_ingredient_id, ri_amount) VALUES (?, ?, ?)", (recipeId, key, ingredients[key]))

	
res = requests.get('https://www.allrecipes.com/recipes/?internalSource=hub%20nav&referringId=78&referringContentType=recipe%20hub&referringPosition=2&linkName=hub%20nav%20exposed&clickId=hub%20nav%202')
soup = bs4.BeautifulSoup(res.text, 'html.parser')

categories = soup.select('.all-categories-col li a')
numRecipes = 0
for i in categories:
	res = requests.get(i.get('href'))
	soup = bs4.BeautifulSoup(res.text, 'html.parser')
	category = i.string
	print("CATEGORY: " + category)
	recipeLink = soup.select('.fixed-recipe-card .grid-card-image-container > a')
	for j in recipeLink:
		numRecipes += 1
		print(numRecipes)
		processRecipe(j['href'], category)
db.commit()
db.close()
# print("done")
