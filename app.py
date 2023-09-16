from flask import Flask, jsonify, request
from bs4 import BeautifulSoup
import urllib.parse
import urllib.request
import ssl
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


class AllRecipes(object):

    @staticmethod
    def search(search_string):
        base_url = "https://allrecipes.com/search?"
        query_url = urllib.parse.urlencode({"q": search_string})

        url = base_url + query_url

        req = urllib.request.Request(url)
        req.add_header('Cookie', 'euConsent=true')

        handler = urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
        opener = urllib.request.build_opener(handler)
        response = opener.open(req)
        html_content = response.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        search_data = []
        articles = soup.findAll("a", {"class": "mntl-card-list-items"})
        articles = [a for a in articles if a["href"].startswith("https://www.allrecipes.com/recipe/")]

        for article in articles:
            data = {}
            try:
                data["name"] = article.find("span", {"class": "card__title"}).get_text().strip(' \t\n\r')
                data["url"] = article['href']
            except:
                pass
            if data:
                search_data.append(data)

        return search_data

    @staticmethod
    def _get_rating(soup):
        try:
            rating_div = soup.find("div", {"id": "mntl-recipe-review-bar__rating_1-0"})
            return float(rating_div.get_text(strip=True))
        except:
            return None

    @staticmethod
    def _get_ingredients(soup):
        ingredient_elements = soup.select("li.mntl-structured-ingredients__list-item")
        ingredients = []
        for el in ingredient_elements:
            quantity = el.find("span", {"data-ingredient-quantity": "true"})
            unit = el.find("span", {"data-ingredient-unit": "true"})
            name = el.find("span", {"data-ingredient-name": "true"})
            ingredients.append(f"{quantity.get_text(strip=True) if quantity else ''} {unit.get_text(strip=True) if unit else ''} {name.get_text(strip=True) if name else ''}".strip())
        return ingredients

    @staticmethod
    def _get_name(soup):
        try:
            return soup.find("h1", {"id": "article-heading_1-0"}).get_text(strip=True)
        except:
            return ""

    @classmethod
    def get(cls, url):
        req = urllib.request.Request(url)
        req.add_header('Cookie', 'euConsent=true')

        handler = urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
        opener = urllib.request.build_opener(handler)
        response = opener.open(req)
        html_content = response.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        data = {"url": url}
        try:
            data["name"] = cls._get_name(soup)
        except:
            data["name"] = ""

        try:
            data["rating"] = cls._get_rating(soup)
        except:
            data["rating"] = "Not available"

        try:
            data["ingredients"] = cls._get_ingredients(soup)
        except:
            data["ingredients"] = []

        return data

@app.route('/search', methods=['GET'])
def search_recipes():
    ingredients = request.args.get('ingredients')
    
    if not ingredients:
        return jsonify({"error": "Ingredients parameter is required"}), 400

    search_string = ingredients.replace(',', ' ')
    recipes = AllRecipes.search(search_string)
    return jsonify(recipes)

@app.route('/details/<path:url>', methods=['GET'])
def get_recipe_details(url):
    details = AllRecipes.get(url)
    return jsonify(details)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
