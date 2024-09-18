import random
from fastapi import FastAPI, Response, HTTPException
from pydantic import BaseModel
from load_models import load_ner_models, load_transformers, load_zero_shot_models
from datetime import date, timedelta
import string
import pandas as pd
from load_models import load_sql
import logging
from dateparser import parse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

transformers = load_transformers()
ner_models = load_ner_models()
zero_shot_models = load_zero_shot_models()

app = FastAPI()

class EmbeddingRequest(BaseModel):
  input: str
  model: str

@app.get("/healthz")
async def healthz():
    return {
        "status": "ok"
    }

@app.get("/models")
async def models():
    models = []

    for model in transformers.keys():
        models.append({
            "id": model,
            "object": "model"
        })

    return {
        "data": models,
        "object": "list"
    }

@app.post("/embeddings")
async def embedding(req: EmbeddingRequest, res: Response):
    if req.model not in transformers:
        raise HTTPException(status_code=400, detail="unknown model: " + req.model)

    embeddings = transformers[req.model].encode([req.input])

    data = []

    for embedding in embeddings.tolist():
        data.append({
            "object": "embedding",
            "embedding": embedding,
            "index": len(data)
        })

    usage = {
        "prompt_tokens": 0,
        "total_tokens": 0,
    }
    return {
        "data": data,
        "model": req.model,
        "object": "list",
        "usage": usage
    }

class NERRequest(BaseModel):
  input: str
  labels: list[str]
  model: str


@app.post("/ner")
async def ner(req: NERRequest, res: Response):
    if req.model not in ner_models:
        raise HTTPException(status_code=400, detail="unknown model: " + req.model)

    model = ner_models[req.model]
    entities = model.predict_entities(req.input, req.labels)

    return {
        "data": entities,
        "model": req.model,
        "object": "list",
    }

class ZeroShotRequest(BaseModel):
  input: str
  labels: list[str]
  model: str


def remove_punctuations(s, lower=True):
    s = s.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    s = " ".join(s.split())
    if lower:
        s = s.lower()
    return s


@app.post("/zeroshot")
async def zeroshot(req: ZeroShotRequest, res: Response):
    if req.model not in zero_shot_models:
        raise HTTPException(status_code=400, detail="unknown model: " + req.model)

    classifier = zero_shot_models[req.model]
    labels_without_punctuations = [remove_punctuations(label) for label in req.labels]
    predicted_classes = classifier(req.input, candidate_labels=labels_without_punctuations, multi_label=True)
    label_map = dict(zip(labels_without_punctuations, req.labels))

    orig_map = [label_map[label] for label in predicted_classes["labels"]]
    final_scores = dict(zip(orig_map, predicted_classes["scores"]))
    predicted_class = label_map[predicted_classes["labels"][0]]

    return {
        "predicted_class": predicted_class,
        "predicted_class_score": final_scores[predicted_class],
        "scores": final_scores,
        "model": req.model,
    }


class WeatherRequest(BaseModel):
  city: str


@app.post("/weather")
async def weather(req: WeatherRequest, res: Response):

    weather_forecast = {
        "city": req.city,
        "temperature": [],
        "unit": "F",
    }
    for i in range(7):
       min_temp = random.randrange(50,90)
       max_temp = random.randrange(min_temp+5, min_temp+20)
       weather_forecast["temperature"].append({
           "date": str(date.today() + timedelta(days=i)),
           "temperature": {
              "min": min_temp,
              "max": max_temp
           }
       })

    return weather_forecast


'''
*****
Adding new functions to test the usecases - Sampreeth
*****
'''

conn = load_sql()
name_col = "name"

class TopEmployees(BaseModel):
    grouping: str
    ranking_criteria: str
    top_n: int


@app.post("/top_employees")
async def top_employees(req: TopEmployees, res: Response):
    name_col = "name"
    # Check if `req.ranking_criteria` is a Text object and extract its value accordingly
    logger.info(f"{'* ' * 50}\n\nCaptured Ranking Criteria: {req.ranking_criteria}\n\n{'* ' * 50}")

    if req.ranking_criteria == "yoe":
        req.ranking_criteria = "years_of_experience"
    elif req.ranking_criteria == "rating":
        req.ranking_criteria = "performance_score"
    
    logger.info(f"{'* ' * 50}\n\nFinal Ranking Criteria: {req.ranking_criteria}\n\n{'* ' * 50}")


    query = f"""
    SELECT {req.grouping}, {name_col}, {req.ranking_criteria}
    FROM (
        SELECT {req.grouping}, {name_col}, {req.ranking_criteria},
               DENSE_RANK() OVER (PARTITION BY {req.grouping} ORDER BY {req.ranking_criteria} DESC) as emp_rank
        FROM employees
    ) ranked_employees
    WHERE emp_rank <= {req.top_n};
    """
    result_df = pd.read_sql_query(query, conn)
    result = result_df.to_dict(orient='records')
    return result


class AggregateStats(BaseModel):
    grouping: str
    aggregate_criteria: str
    aggregate_type: str

@app.post("/aggregate_stats")
async def aggregate_stats(req: AggregateStats, res: Response):
    logger.info(f"{'* ' * 50}\n\nCaptured Aggregate Criteria: {req.aggregate_criteria}\n\n{'* ' * 50}")

    if req.aggregate_criteria == "yoe":
        req.aggregate_criteria = "years_of_experience"

    logger.info(f"{'* ' * 50}\n\nFinal Aggregate Criteria: {req.aggregate_criteria}\n\n{'* ' * 50}")

    logger.info(f"{'* ' * 50}\n\nCaptured Aggregate Type: {req.aggregate_type}\n\n{'* ' * 50}")
    if req.aggregate_type.lower() not in ["sum", "avg", "min", "max"]:
        if req.aggregate_type.lower() == "count":
            req.aggregate_type = "COUNT"
        elif req.aggregate_type.lower() == "total":
            req.aggregate_type = "SUM"
        elif req.aggregate_type.lower() == "average":
            req.aggregate_type = "AVG"
        elif req.aggregate_type.lower() == "minimum":
            req.aggregate_type = "MIN"
        elif req.aggregate_type.lower() == "maximum":
            req.aggregate_type = "MAX"
        else:
            raise HTTPException(status_code=400, detail="Invalid aggregate type")
    
    logger.info(f"{'* ' * 50}\n\nFinal Aggregate Type: {req.aggregate_type}\n\n{'* ' * 50}")

    query = f"""
    SELECT {req.grouping}, {req.aggregate_type}({req.aggregate_criteria}) as {req.aggregate_type}_{req.aggregate_criteria}
    FROM employees
    GROUP BY {req.grouping};
    """
    result_df = pd.read_sql_query(query, conn)
    result = result_df.to_dict(orient='records')
    return result

class PacketDropCorrelationRequest(BaseModel):
    from_time: str = None  # Optional natural language timeframe
    ifname: str = None     # Optional interface name filter
    region: str = None     # Optional region filter
    min_in_errors: int = None
    max_in_errors: int = None
    min_out_errors: int = None
    max_out_errors: int = None
    min_in_discards: int = None
    max_in_discards: int = None
    min_out_discards: int = None
    max_out_discards: int = None


@app.post("/interface_down_pkt_drop")
async def interface_down_pkt_drop(req: PacketDropCorrelationRequest, res: Response):
    # Step 1: Convert the from_time natural language string to a timestamp if provided
    if req.from_time:
        # Use `dateparser` to parse natural language timeframes
        parsed_time = parse(req.from_time, settings={'RELATIVE_BASE': datetime.datetime.now()})
        if not parsed_time:
            return {"error": "Invalid from_time format. Please provide a valid time description such as 'past 7 days' or 'since last month'."}
        from_time = parsed_time
        logger.info(f"Using parsed from_time: {from_time}")
    else:
        # If no from_time is provided, use a default value (e.g., the past 7 days)
        from_time = datetime.datetime.now() - datetime.timedelta(days=7)
        logger.info(f"Using default from_time: {from_time}")

    # Step 2: Build the dynamic SQL query based on the optional filters
    filters = []
    params = {"from_time": from_time}

    if req.ifname:
        filters.append("i.ifname = :ifname")
        params["ifname"] = req.ifname

    if req.region:
        filters.append("d.region = :region")
        params["region"] = req.region

    if req.min_in_errors is not None:
        filters.append("i.in_errors >= :min_in_errors")
        params["min_in_errors"] = req.min_in_errors

    if req.max_in_errors is not None:
        filters.append("i.in_errors <= :max_in_errors")
        params["max_in_errors"] = req.max_in_errors

    if req.min_out_errors is not None:
        filters.append("i.out_errors >= :min_out_errors")
        params["min_out_errors"] = req.min_out_errors

    if req.max_out_errors is not None:
        filters.append("i.out_errors <= :max_out_errors")
        params["max_out_errors"] = req.max_out_errors

    if req.min_in_discards is not None:
        filters.append("i.in_discards >= :min_in_discards")
        params["min_in_discards"] = req.min_in_discards

    if req.max_in_discards is not None:
        filters.append("i.in_discards <= :max_in_discards")
        params["max_in_discards"] = req.max_in_discards

    if req.min_out_discards is not None:
        filters.append("i.out_discards >= :min_out_discards")
        params["min_out_discards"] = req.min_out_discards

    if req.max_out_discards is not None:
        filters.append("i.out_discards <= :max_out_discards")
        params["max_out_discards"] = req.max_out_discards

    # Join the filters using AND
    where_clause = " AND ".join(filters)
    if where_clause:
        where_clause = "AND " + where_clause

    # Step 3: Query packet errors and flows from interfacestats and ts_flow
    query = f"""
    SELECT
      d.switchip AS device_ip_address,
      i.in_errors,
      i.in_discards,
      i.out_errors,
      i.out_discards,
      i.ifname,
      t.src_addr,
      t.dst_addr,
      t.time AS flow_time,
      i.time AS interface_time
    FROM
      device d
    INNER JOIN
      interfacestats i
      ON d.device_mac_address = i.device_mac_address
    INNER JOIN
      ts_flow t
      ON d.switchip = t.sampler_address
    WHERE
      i.time >= :from_time  -- Using the converted timestamp
      {where_clause}
    ORDER BY
      i.time;
    """

    correlated_data = pd.read_sql_query(query, conn, params=params)
    
    if correlated_data.empty:
        return {"message": "No correlated packet drops found"}

    logger.info(f"Correlated Packet Drop Data: {correlated_data}")

    return correlated_data.to_dict(orient='records')