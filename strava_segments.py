import requests
import polyline
import folium
from geopy.distance import distance
import math


# Function to retrieve the list of Strava segments within a given area
def get_segments(sw_lat, sw_lng, ne_lat, ne_lng):
    url = f"https://www.doogal.co.uk/StravaSegments?swLat={sw_lat}&swLng={sw_lng}&neLat={ne_lat}&neLng={ne_lng}&type=riding&min_cat=0&orderBy=nearest"
    response = requests.get(url)
    segments = response.json()
    return segments

# Function to retrieve wind forecast data for a given location and time range
def get_wind_forecast(latitude, longitude, forecast_days=1):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=windspeed_10m,winddirection_10m&forecast_days={forecast_days}"
    response = requests.get(url)
    forecast_data = response.json()
    hourly_forecast = []
    for i in range(len(forecast_data['hourly']['time'])):
        hourly = forecast_data['hourly']['time'][i]
        windspeed = forecast_data['hourly']['windspeed_10m'][i]
        winddirection = forecast_data['hourly']['winddirection_10m'][i]
        hourly_forecast.append((hourly, windspeed, winddirection))
    return hourly_forecast

# Function to calculate the angle between wind and segment directions (in degrees)
def angle_between(wind_dir1, wind_dir2):
    diff = (wind_dir1 - wind_dir2 + 180) % 360 - 180
    return abs(diff)

# Function to calculate segment direction between the first and the last point (in degrees)
def calculate_bearing(point1, point2):
    lat1, lon1 = point1
    lat2, lon2 = point2
    d_lon = lon2 - lon1
    y = math.sin(math.radians(d_lon)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(d_lon))
    bearing = math.atan2(y, x)
    return math.degrees(bearing)

# Function to filter the list of Strava segments by wind conditions (within max_angle)
def filter_segments_by_wind(segments, wind_speed, wind_dir, max_angle=45):
    filtered_segments = []
    for segment in segments:
        polyline_str = segment["map"]["polyline"]
        points = polyline.decode(polyline_str)
        # Calculate the distance and initial bearing between the two points
        #dist = distance(points[0], points[-1]).km #to check later if the segment is a loop
        segment_dir = calculate_bearing(points[0], points[-1])
        angle = angle_between(segment_dir, wind_dir)
        if angle <= max_angle:
            filtered_segments.append(segment)           
    return filtered_segments

# Function to create a map showing the filtered segments
def create_map(segments, wind_speed, wind_dir, center_lat, center_lng):
    m = folium.Map(location=[center_lat, center_lng], zoom_start=12)
    for segment in segments:
        polyline_str = segment["map"]["polyline"]
        points = polyline.decode(polyline_str)
        folium.PolyLine(points, color="black", weight=3, opacity=0.7, tooltip=segment["name"]).add_to(m)
    # create arrow marker
    folium.Marker(location=[center_lat, center_lng],
                  icon=folium.Icon(icon="arrow-up", prefix='fa'),
                  tooltip=f"Wind speed: {wind_speed} km/h\nWind direction: {wind_dir}°"
                 ).add_to(m)
    return m

# Define the area to search for segments (in this example, a rectangle around Joensuu)
sw_lat, sw_lng = 62.55564688130491, 29.704366223835024
ne_lat, ne_lng = 62.61631266792659, 29.91738266265719

# Retrieve the list of segments in the area
segments = get_segments(sw_lat, sw_lng, ne_lat, ne_lng)

# Retrieve wind forecast data for the center of the area
center_lat = (sw_lat + ne_lat) / 2
center_lng = (sw_lng + ne_lng) / 2
forecast_data = get_wind_forecast(center_lat, center_lng)

#current wind speed and direction
wind_speed = forecast_data[0][1]
wind_dir = forecast_data[0][2]

#Filter the list of segments by wind conditions
filtered_segments = filter_segments_by_wind(segments, wind_speed, wind_dir)

#Create a map showing the filtered segments
m = create_map(filtered_segments, wind_speed, wind_dir, center_lat, center_lng)
m.save("my_map.html")