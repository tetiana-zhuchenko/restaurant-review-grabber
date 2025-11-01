import requests
import json
import time
import os
from pathlib import Path

API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')

def load_api_key_from_file():
    """Load API key from a config file that's not in git"""
    config_file = Path('config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
            print(config.get('google_places_api_key'))
            return config.get('google_places_api_key')
    return None

# Try both methods
if not API_KEY:
    API_KEY = load_api_key_from_file()

# Validate API key
if not API_KEY:
    print("❌ ERROR: No API key found!")
    exit(1)

def search_restaurants(query, max_results=20):
    """
    Searches for restaurants using Text Search (New) API.
    Returns up to max_results restaurants (API limit is 20 per request).
    """
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.id,places.formattedAddress"
    }
    data = {
        "textQuery": query,
        "maxResultCount": min(max_results, 20),  # API limit is 20
        "languageCode": "uk",
        "regionCode": "UA"
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def collect_restaurant_ids(cities, restaurant_types, max_per_search=20):
    """
    Collect restaurant IDs from multiple cities and restaurant types
    """
    all_restaurants = []
    unique_place_ids = set()  # To avoid duplicates
    
    total_searches = len(cities) * len(restaurant_types)
    current_search = 0
    
    print(f"🔍 Starting collection from {len(cities)} cities and {len(restaurant_types)} restaurant types")
    print(f"📊 Total searches planned: {total_searches}")
    print("=" * 60)
    
    for city in cities:
        print(f"\n🏙️ Processing city: {city}")
        
        for restaurant_type in restaurant_types:
            current_search += 1
            query = f"{restaurant_type} у {city}"
            
            print(f"   [{current_search}/{total_searches}] Searching: {query}")
            
            try:
                search_results = search_restaurants(query, max_per_search)
                
                if search_results and 'places' in search_results:
                    places = search_results['places']
                    new_places = 0
                    
                    for place in places:
                        place_id = place['id']
                        
                        # Skip if we already have this restaurant
                        if place_id not in unique_place_ids:
                            restaurant_info = {
                                'place_id': place_id,
                                'name': place['displayName']['text'],
                                'address': place.get('formattedAddress', 'Unknown'),
                                'city': city,
                                'restaurant_type': restaurant_type,
                                'search_query': query
                            }
                            
                            all_restaurants.append(restaurant_info)
                            unique_place_ids.add(place_id)
                            new_places += 1
                    
                    print(f"      ✅ Found {len(places)} places, {new_places} new unique restaurants")
                else:
                    print(f"      ⚠️ No results found")
                
                time.sleep(0.3)  # Rate limiting between searches
                
            except Exception as e:
                print(f"      ❌ Search failed: {e}")
                continue
    
    print("\n" + "=" * 60)
    print(f"📋 RESTAURANT ID COLLECTION SUMMARY:")
    print(f"   Total unique restaurants found: {len(all_restaurants)}")
    print(f"   Cities covered: {len(cities)}")
    print(f"   Restaurant types searched: {len(restaurant_types)}")
    
    return all_restaurants

def get_place_details_ukrainian_reviews(place_id):
    """
    Fetches details, including reviews, for a given place_id
    """
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "reviews,displayName,formattedAddress,rating,userRatingCount,websiteUri,currentOpeningHours"
        
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def collect_reviews_from_restaurants(restaurants_list):
    """
    Collect reviews from a list of restaurants
    """
    all_collected_reviews = []
    ukrainian_only_reviews_dataset = []
    
    total_restaurants = len(restaurants_list)
    print(f"\n📝 Starting review collection from {total_restaurants} restaurants")
    print("=" * 60)
    
    for i, restaurant in enumerate(restaurants_list, 1):
        place_id = restaurant['place_id']
        place_name = restaurant['name']
        city = restaurant['city']
        
        print(f"[{i}/{total_restaurants}] {place_name} ({city})")
        
        try:
            details = get_place_details_ukrainian_reviews(place_id)
            
            if 'reviews' in details:
                reviews_count = len(details['reviews'])
                print(f"   📄 Found {reviews_count} reviews")
                
                ukrainian_count = 0
                for review in details['reviews']:
                    review_text = review.get('text', {}).get('text')
                    review_lang_code = review.get('text', {}).get('languageCode')

                    review_data = {
                        "restaurant_name": place_name,
                        "restaurant_city": city,
                        "restaurant_type": restaurant['restaurant_type'],
                        "restaurant_address": restaurant['address'],
                        "place_id": place_id,
                        "review_author": review.get('authorAttribution', {}).get('displayName'),
                        "review_rating": review.get('rating'),
                        "review_text": review_text,
                        "review_time": review.get('publishTime'),
                        "review_language_code": review_lang_code
                    }
                    all_collected_reviews.append(review_data)

                    # Filter for Ukrainian reviews
                    if review_lang_code == 'uk':
                        ukrainian_only_reviews_dataset.append(review_data)
                        ukrainian_count += 1
                
                if ukrainian_count > 0:
                    print(f"   🇺🇦 {ukrainian_count} Ukrainian reviews found!")
                else:
                    print(f"   ⚪ No Ukrainian reviews")
            else:
                print(f"   ⚠️ No reviews found")

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    return all_collected_reviews, ukrainian_only_reviews_dataset

def save_restaurant_ids(restaurants_list, filename="restaurant_ids.json"):
    """
    Save the collected restaurant IDs to a file
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(restaurants_list, f, ensure_ascii=False, indent=2)
    print(f"💾 Restaurant IDs saved to: {filename}")

def load_restaurant_ids(filename="restaurant_ids.json"):
    """
    Load restaurant IDs from a file
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File {filename} not found")
        return []

# --- Main script ---
if __name__ == "__main__":
    # Configuration for Ukrainian cities
    ukrainian_cities = [
        "Київ",
        "Львів", 
        "Одеса",
        "Харків",
        "Дніпро"
    ]
    
    restaurant_types = [
        "ресторан",
        "кафе", 
        "піцерія",
        "суші ресторан",
        "український ресторан",
        "італійський ресторан"
    ]
    
    print("🇺🇦 Ukrainian Restaurant Reviews Collector")
    print("=" * 50)
    print("Choose an option:")
    print("1. Collect restaurant IDs only")
    print("2. Collect restaurant IDs + reviews")
    print("3. Load existing IDs and collect reviews")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        # Just collect restaurant IDs
        print("\n🔍 Collecting restaurant IDs...")
        restaurants = collect_restaurant_ids(ukrainian_cities, restaurant_types, max_per_search=20)
        
        if restaurants:
            save_restaurant_ids(restaurants)
            
            # Show some examples
            print(f"\n📋 Sample restaurants found:")
            for i, rest in enumerate(restaurants[:5], 1):
                print(f"{i}. {rest['name']} ({rest['city']}) - {rest['restaurant_type']}")
            
            print(f"\n🎉 Successfully collected {len(restaurants)} restaurant IDs!")
            print("💡 Run option 3 later to collect reviews from these restaurants.")
        
    elif choice == "2":
        # Collect IDs and reviews in one go
        print("\n🔍 Collecting restaurant IDs...")
        restaurants = collect_restaurant_ids(ukrainian_cities, restaurant_types, max_per_search=20)
        
        if restaurants:
            save_restaurant_ids(restaurants)
            
            print(f"\n📝 Now collecting reviews from {len(restaurants)} restaurants...")
            all_reviews, ukrainian_reviews = collect_reviews_from_restaurants(restaurants)
            
            # Save results
            print("\n💾 Saving datasets...")
            with open("restaurant_reviews_all_languages.json", "w", encoding="utf-8") as f:
                json.dump(all_reviews, f, ensure_ascii=False, indent=2)
            print("✅ All reviews saved to: restaurant_reviews_all_languages.json")

            if ukrainian_reviews:
                with open("restaurant_reviews_ukrainian_only.json", "w", encoding="utf-8") as f:
                    json.dump(ukrainian_reviews, f, ensure_ascii=False, indent=2)
                print("✅ Ukrainian reviews saved to: restaurant_reviews_ukrainian_only.json")
                print(f"\n🎉 SUCCESS! Collected {len(ukrainian_reviews)} Ukrainian reviews from {len(restaurants)} restaurants!")
            else:
                print("\n⚠️ No Ukrainian reviews found.")
    
    elif choice == "3":
        # Load existing IDs and collect reviews
        restaurants = load_restaurant_ids()
        
        if restaurants:
            print(f"\n📂 Loaded {len(restaurants)} restaurants from file")
            print(f"📝 Starting review collection...")
            
            all_reviews, ukrainian_reviews = collect_reviews_from_restaurants(restaurants)
            
            # Save results
            print("\n💾 Saving datasets...")
            with open("restaurant_reviews_all_languages.json", "w", encoding="utf-8") as f:
                json.dump(all_reviews, f, ensure_ascii=False, indent=2)
            print("✅ All reviews saved to: restaurant_reviews_all_languages.json")

            if ukrainian_reviews:
                with open("restaurant_reviews_ukrainian_only.json", "w", encoding="utf-8") as f:
                    json.dump(ukrainian_reviews, f, ensure_ascii=False, indent=2)
                print("✅ Ukrainian reviews saved to: restaurant_reviews_ukrainian_only.json")
                print(f"\n🎉 SUCCESS! Collected {len(ukrainian_reviews)} Ukrainian reviews!")
            else:
                print("\n⚠️ No Ukrainian reviews found.")
        else:
            print("❌ No restaurant IDs found. Run option 1 or 2 first.")
    
    else:
        print("❌ Invalid choice. Please run the script again and choose 1, 2, or 3.")