import duckdb

con = duckdb.connect("taxi.db")

print("Question 2 - What's the average trip distance for rides with 2 passengers?")
result = con.execute("""
    SELECT AVG(trip_distance)
    FROM trips
    WHERE passenger_count = 2;
""").fetchone()

print(result)


print("Question 3 - How many rides had more than 5 passengers?")
result = con.execute("""
    SELECT COUNT(*)
    FROM trips
    WHERE passenger_count > 5;
""").fetchone()
print(result)

print("Question 5 - Which hour of the day has the highest average fare amount?")
result = con.execute("""
    SELECT EXTRACT(HOUR FROM tpep_pickup_datetime) AS hour,
       AVG(fare_amount) AS avg_fare
    FROM trips
    GROUP BY hour
    ORDER BY avg_fare DESC
    LIMIT 1;
""").fetchone()
print(result)

print("Question 6 - What is the average tip amount for rides paid with a credit card?")
result = con.execute("""
    SELECT AVG(tip_amount)
    FROM trips
    WHERE payment_type = 1
""").fetchone()
print(result)

print("Question 7 - Which pickup location has the most trips?")
result = con.execute("""
    SELECT PULocationID, COUNT(*) as trip_count
FROM trips
GROUP BY PULocationID
ORDER BY trip_count DESC
LIMIT 1
""").fetchone()
print(result)

print("Question 8 - What is the average fare amount for trips longer than 10 miles?")
result = con.execute("""
    SELECT AVG(fare_amount)
    FROM trips
    WHERE trip_distance > 10
""").fetchone()
print(result)

print("Question 9 - How many trips had zero passengers recorded?")
result = con.execute("""
    SELECT COUNT(*)
    FROM trips
    WHERE passenger_count = 0
""").fetchone()
print(result)

print("Question 10 - What is the busiest day of the week for taxi trips?")
result = con.execute("""
    SELECT strftime('%w', tpep_pickup_datetime) as day_of_week,
       COUNT(*) as trip_count
    FROM trips
    GROUP BY day_of_week
    ORDER BY trip_count DESC
    LIMIT 1
""").fetchone()
print(result)