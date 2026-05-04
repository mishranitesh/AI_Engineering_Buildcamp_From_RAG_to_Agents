# Homework (mini-project) - Week3 

In this homework we'll build an agent that can search Wikipedia and fetch page content to answer questions.

We'll start by defining tools, then create an agent that uses these tools to answer questions about any topic.


## Wikipedia API Setup

We'll use two Wikipedia API endpoints.

### Search API - Find pages related to a topic:

```javascript
https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch=YOUR_QUERY
```

Replace YOUR_QUERY with your search term. Use + for spaces (for example, lesser+capybara).

### Get Page API - Fetch the raw content of a page:

```javascript
https://en.wikipedia.org/w/index.php?title=PAGE_TITLE&action=raw
```

Replace PAGE_TITLE with the exact title of the Wikipedia page.

### Wikipedia requires a User-Agent header on API requests. Without it, your requests may be blocked. Pass it in every requests.get call:

```python
import requests

headers = {"User-Agent": "ai-engineering-buildcamp/1.0 (educational project)"}
response = requests.get(url, headers=headers)
```

## Wikipedia Agent

A simple AI agent that can:

- Search Wikipedia
- Fetch page content
- Answer questions using tool calls

Built using:
- PydanticAI
- OpenAI GPT-4.1-mini
- Wikipedia APIs

### Project structure

```
week3_wikipedia_agent/
│
├── app.py  # Main entry point. Runs the agent and asks questions.
├── requirements.txt
├── .env
├── README.md
│
├── tools/ # Keep tools isolated from agent logic.
│   ├── __init__.py
│   ├── wikipedia_search.py
│   └── wikipedia_page.py
│
├── agent/ # Agent setup only.
│   ├── __init__.py
│   └── wikipedia_agent.py
│
├── tests/
│   ├── test_search.py
│   └── test_page.py
│
└── utils/ # Useful later for API keys/config.
    ├── __init__.py
    └── config.py
```

### Install Dependencies
```bash
pip install pydantic-ai requests python-dotenv
```

### Question 1. Define the Search Tool

Create a search_wikipedia function that:

- Takes a query string as input
- Calls the Wikipedia Search API
- Returns the search results

Test your function with the query "capybara".

How many total results did the search return?

- 5
- 10 <-- answer
- 15
- 20

Hint: Look at the query.search array in the JSON response.

#### Steps followed - 

```bash
# Create Virtual Environment and activate it
python -m venv .venv
source .venv/bin/activate

pip install requests

# Add Search Tool, file - tools/wikipedia_search.py

# Add Main Runner, file - app.py

from tools.wikipedia_search import search_wikipedia

results = search_wikipedia("capybara")
search_items = results["query"]["search"]
print(f"Total results: {len(search_items)}")
print("\nTitles:\n")

for item in search_items:
    print("-", item["title"])

# Run the Project
python app.py

# Output
Total results: 10

Titles:

- Capybara
- Lesser capybara
- Capybara (disambiguation)
- Capybara Games
- Hydrochoerus
- Capybara (software)
- Caviidae
- Flow (2024 film)
- Yuzu bath
- Kerodon
```


### Question 2. Analyzing Search Results

Using your search_wikipedia function, search for "capybara" again.

Look at the titles in the search results. How many of the results contain the word "capybara" (case-insensitive) in their title?

- 3
- 5 <-- answer
- 7
- 9

Hint: Check each result's title field.

#### Steps followed -

```bash
# Update Main Runner, file - app.py, update with - 
count = 0

for item in search_items:

    title = item["title"]

    if "capybara" in title.lower():
        count += 1

print(f"\nTitles containing 'capybara': {count}")

# Run the Project
python app.py

# Output
Total results: 10

Titles:

- Capybara
- Lesser capybara
- Capybara (disambiguation)
- Capybara Games
- Hydrochoerus
- Caviidae
- Flow (2024 film)
- Capybara (software)
- Yuzu bath
- Kerodon

Titles containing 'capybara': 5
```


### Question 3. Define the Get Page Tool

Create a get_page function that:
- 
- Takes a page title as input
- Calls the Wikipedia Get Page API
- Returns the page content as a string
 

Test your function by fetching the page titled "Capybara".

How many characters are in the page content?

- ~5,000
- ~15,000
- ~25,000
- ~35,000 <-- answer

Hint: Use len(content) to count characters.

```bash
# Update Main Runner, file - app.py, update with - 

content = get_page("Capybara")

print("\nCharacter count:")
print(len(content))

# Run the Project
python app.py

# Output
(.venv) niteshmishra@Mac week3 % python app.py
Total results: 10

Titles:

- Capybara
- Lesser capybara
- Capybara (disambiguation)
- Capybara Games
- Hydrochoerus
- Caviidae
- Capybara (software)
- Flow (2024 film)
- Yuzu bath
- Kerodon

Titles containing 'capybara': 5

Character count:
36946
```


Note: Wikipedia pages can be long. If you're using a smaller or free model with a limited context window, you may need to chunk the page content and only send the most relevant chunk to the LLM. The right chunk size depends on your model's input token limit.

### Question 4. Agent Setup

Now create an agent with access to both tools:

- search_wikipedia - Search for Wikipedia pages
- get_page - Fetch the content of a specific page

You can use any framework (ToyAIKit, PydanticAI, OpenAI Agents SDK, LangChain, etc.) or implement the agentic loop yourself from scratch. 

You can also use any LLM provider (OpenAI, Anthropic, AWS Bedrock, etc.).

In your submission, please specify:

- Which framework did you choose (or "custom" if implementing from scratch)?
- Which LLM provider did you use?

This question is for tracking purposes - any reasonable choice is correct.

If you don't know what to choose, I recommend PydanticAI + OpenAI.

Which framework and LLM provider did you choose for this homework?


#### Answer
- Framework: PydanticAI
- LLM Provider: OpenAI

### Question 5. Testing Your Agent - Single Page

Use your agent to answer this question:

"What is this page about? https://en.wikipedia.org/wiki/Capybara"

Your agent should:

- Use the get_page tool to fetch the Capybara page
- Provide a concise summary of what the page is about

What is the main topic of the Capybara page according to your agent?

Write the answer to the homework form.

#### Steps followed

```bash
# Install Dependencies
pip install -r requirements.txt

# Create Agent File - agent/wikipedia_agent.py

# Update app.py
from agent.wikipedia_agent import agent

result = agent.run_sync(
    "What is this page about? https://en.wikipedia.org/wiki/Capybara"
)
print(result.output)

# Run agent
python app.py

# Output
The Wikipedia page is about the capybara (Hydrochoerus hydrochaeris), the largest living rodent native to South America. The page provides detailed information about the capybara's taxonomy, physical description, ecology, behavior, diet, social organization, reproduction, conservation status, and interactions with humans. It highlights that capybaras are semiaquatic herbivores native to most South American countries, living in groups near water bodies. The page also describes their anatomy, social behavior, vocalizations, and reproduction. Capybaras are hunted for meat and hides but are considered of least concern conservation-wise due to their stable population. They have adapted well to urban environments and have cultural significance in places like Japan and Venezuela. Additionally, capybaras have a notable presence in internet meme culture and popular media.
```

Expected Behavior

The agent should:

- recognize it needs page content
- call wiki_get_page
- summarize the article

### Question 6. Testing Your Agent - Search Then Fetch

Now let's test if your agent can use both tools together.

Ask your agent:

"What are the main threats to capybara populations?"

Your agent should:

- First use search_wikipedia to find pages about capybara threats
- Then use get_page to fetch the relevant pages and extract specific threat information

- How many total tool calls (search + fetch combined) did your agent make?

In your answer, provide:

- Which tools it used and in what order
- The final answer your agent gave

#### Steps followed 

```bash
# Update app.py
from agent.wikipedia_agent import agent


result = agent.run_sync(
    "What are the main threats to capybara populations?"
)

print("\nFINAL ANSWER:\n")
print(result.output)


print("\n--- TOOL TRACE ---\n")

for msg in result.all_messages():
    print(msg)
    print("-" * 50)
```

#### Output
```
FINAL ANSWER:

The main threats to capybara populations include:

1. Hunting: Capybaras are hunted for their meat and hide in some areas. Hunting has reduced their numbers in certain regions.
2. Competition and Human Conflict: They are sometimes killed by humans who see their grazing as competition for livestock.
3. Habitat Disturbance: Urbanization and habitat destruction can disrupt their natural wetland habitats, although capybaras have shown some adaptation to urban environments.

Despite these threats, capybaras are not currently considered a threatened species, and their population is generally stable throughout most of their South American range. Their ability to breed rapidly also aids their survival. In some places, capybaras are farmed, which helps protect their wetland habitats.

--- TOOL TRACE ---

ModelRequest(parts=[SystemPromptPart(content='\n    You are a helpful Wikipedia research assistant.\n\n    You can:\n    - search Wikipedia pages\n    - fetch Wikipedia page content\n    - answer user questions using the tools provided\n    ', timestamp=datetime.datetime(2026, 5, 4, 22, 17, 43, 199745, tzinfo=datetime.timezone.utc)), UserPromptPart(content='What are the main threats to capybara populations?', timestamp=datetime.datetime(2026, 5, 4, 22, 17, 43, 199754, tzinfo=datetime.timezone.utc))], timestamp=datetime.datetime(2026, 5, 4, 22, 17, 43, 199893, tzinfo=datetime.timezone.utc), run_id='019df511-941d-75de-9f54-6544f1917fbc', conversation_id='019df511-941d-75de-9f54-654395292aa2')
--------------------------------------------------
ModelResponse(parts=[ToolCallPart(tool_name='wiki_search', args='{"query":"capybara threats"}', tool_call_id='call_ntVb94cM45MlcHwEOMEqU0AZ')], usage=RequestUsage(input_tokens=100, output_tokens=18, details={'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}), model_name='gpt-4.1-mini-2025-04-14', timestamp=datetime.datetime(2026, 5, 4, 22, 17, 45, 205212, tzinfo=datetime.timezone.utc), provider_name='openai', provider_url='https://api.openai.com/v1/', provider_details={'finish_reason': 'tool_calls', 'timestamp': datetime.datetime(2026, 5, 4, 22, 17, 44, tzinfo=TzInfo(0))}, provider_response_id='chatcmpl-DbvtgcoZTn9zHGBMwc5LNNm5KQ6ZG', finish_reason='tool_call', run_id='019df511-941d-75de-9f54-6544f1917fbc', conversation_id='019df511-941d-75de-9f54-654395292aa2')
--------------------------------------------------
ModelRequest(parts=[ToolReturnPart(tool_name='wiki_search', content='Sons of Anarchy season 1\nPantanal\nRock cavy\nAquatic mammal\nRodent\nYacare caiman\nGuiana Amazonian Park\nBlue Whale Challenge\nMight and Magic\nPairi Daiza', tool_call_id='call_ntVb94cM45MlcHwEOMEqU0AZ', timestamp=datetime.datetime(2026, 5, 4, 22, 17, 45, 499900, tzinfo=datetime.timezone.utc))], timestamp=datetime.datetime(2026, 5, 4, 22, 17, 45, 500831, tzinfo=datetime.timezone.utc), run_id='019df511-941d-75de-9f54-6544f1917fbc', conversation_id='019df511-941d-75de-9f54-654395292aa2')
--------------------------------------------------
ModelResponse(parts=[ToolCallPart(tool_name='wiki_get_page', args='{"title":"Capybara"}', tool_call_id='call_tnGby2t392oBFuIWvFp1Nv9o')], usage=RequestUsage(input_tokens=175, output_tokens=18, details={'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}), model_name='gpt-4.1-mini-2025-04-14', timestamp=datetime.datetime(2026, 5, 4, 22, 17, 45, 995826, tzinfo=datetime.timezone.utc), provider_name='openai', provider_url='https://api.openai.com/v1/', provider_details={'finish_reason': 'tool_calls', 'timestamp': datetime.datetime(2026, 5, 4, 22, 17, 45, tzinfo=TzInfo(0))}, provider_response_id='chatcmpl-DbvthHPBVwu0dwl7gumAAz0MqovVh', finish_reason='tool_call', run_id='019df511-941d-75de-9f54-6544f1917fbc', conversation_id='019df511-941d-75de-9f54-654395292aa2')
--------------------------------------------------
ModelRequest(parts=[ToolReturnPart(tool_name='wiki_get_page', content='{{Short description|Largest species of rodents}}\n{{Other uses}}\n{{Good article}}\n{{pp|small=yes}}\n{{Use dmy dates|date=July 2022}}\n{{Speciesbox\n| status = LC\n| status_system = IUCN3.1\n| status_ref = <ref name="iucn">{{cite iucn |author=Reid, F. |year=2016 |title=\'\'Hydrochoerus hydrochaeris\'\' |article-number=e.T10300A22190005 |doi=10.2305/IUCN.UK.2016-2.RLTS.T10300A22190005.en}}</ref>\n| image = Capybaracropped.jpg\n| image_caption = In [[Encontro das Águas State Park]], Brazil\n| genus = Hydrochoerus\n| species = hydrochaeris\n| authority = ([[Carl Linnaeus|Linnaeus]], [[12th edition of Systema Naturae|1766]])\n| range_map = Capybara range.svg\n| range_map_caption = Native range\n| synonyms = \'\'Sus hydrochaeris\'\' {{small|Linnaeus,&nbsp;1766}}\n}}\n\nThe \'\'\'capybara\'\'\'{{efn |Other names include \'\'\'capivara\'\'\' (in Brazil), \'\'\'capiguara\'\'\' (in Bolivia), \'\'\'chigüire\'\'\', \'\'\'chigüiro\'\'\', and \'\'\'fercho\'\'\' (in Colombia and Venezuela), \'\'\'carpincho\'\'\' (in Argentina, Paraguay and Uruguay) and \'\'\'ronsoco\'\'\' (in Peru).}} or \'\'\'greater capybara\'\'\' (\'\'\'\'\'Hydrochoerus hydrochaeris\'\'\'\'\') is the largest living [[rodent]],<ref>{{Cite web | author= Basic Biology | date= 2015 | title= Rodents | url= https://basicbiology.net/animal/mammals/rodents}}</ref> native to all countries in [[South America]] except [[Chile]]. It is a [[semiaquatic]] [[herbivore]] that inhabits savannas and dense forests, living near and in bodies of water and feeding mainly on [[Grass|grasses]] and [[Aquatic plant|aquatic plants]]. \n\nTogether with the [[lesser capybara]], it constitutes the genus \'\'[[Hydrochoerus]]\'\'. Its other close relatives include [[Cavia|guinea pigs]] and [[Kerodon|rock cavies]], and it is more distantly related to the [[agouti]], the [[chinchilla]], and the [[nutria]].\n\nThe capybara is a highly [[Sociality|social]] species that usually lives in groups of 10–20 individuals, but can be found in groups as large as one hundred. It is hunted for its meat and hide and for grease from its thick fatty skin.<ref>[http://www.arkive.org/capybara/hydrochoerus-hydrochaeris/ Capybara (\'\'Hydrochoerus hydrochaeris\'\')] {{Webarchive|url=https://web.archive.org/web/20120103075238/http://www.arkive.org/capybara/hydrochoerus-hydrochaeris/ |date=2012-01-03 }}. ARKive.org</ref>\n\n==Etymology==\nIts common name is derived from [[Tupi language|Tupi]] {{lang|tpn|ka\'apiûara}}, a complex agglutination of {{lang|tpn|kaá}} (leaf) + {{lang|tpn|píi}} (slender) + {{lang|tpn|ú}} (eat) + {{lang|tpn|ara}} (a suffix for agent nouns), meaning "one who eats slender leaves", or "grass-eater".<ref>Ferreira, A. B. H. (1986) \'\'[[Novo Dicionário da Língua Portuguesa]]\'\', 2nd ed., Rio de Janeiro: Nova Fronteira, p.344</ref> The [[genus name]], \'\'hydrochoerus\'\', comes from [[Ancient Greek|Greek]] {{lang|grc|ὕδωρ}} (\'\'{{lang|grc-Latn|hýdor}}\'\' "water") and {{lang|grc|χοῖρος}} (\'\'{{lang|grc-Latn|choíros}}\'\' "pig, hog") and the species name, \'\'hydrochaeris\'\', comes from Greek {{lang|grc|ὕδωρ}} (\'\'{{lang|grc-Latn|hýdor}}\'\' "water") and {{lang|grc|χαίρω}} (\'\'{{lang|grc-Latn|chairo}}\'\' "feel happy, enjoy").<ref name=msw3>{{MSW3 Woods|id=13400218|page=1556}}</ref><ref name="Darwin-1839">{{Cite book | last=Darwin | first=Charles R. | author-link =Charles Darwin| year=1839 | title=Narrative of the surveying voyages of His Majesty\'s Ships Adventure and Beagle between the years 1826 and 1836, describing their examination of the southern shores of South America, and the Beagle\'s circumnavigation of the globe. Journal and remarks. 1832–1836. | title-link =The Voyage of the Beagle| place =London | publisher =[[Henry Colburn]] | page=619}}\n* In page 57, Darwin says "The largest gnawing animal in the world, the \'\'Hydrochærus Capybara\'\' (the water-hog), is here also common."\n* See it also in [http://darwin-online.org.uk/content/frameset?itemID=F10.3&viewtype=side&pageseq=1 The Complete Work of Charles Darwin Online]</ref>\n\n==Classification and phylogeny==\nThe capybara and the [[lesser capybara]] both belong to the subfamily [[Hydrochoerinae]] along with the [[Kerodon|rock cavies]]. The living capybaras and their extinct relatives were previously classified in their own family Hydrochoeridae.<ref name="Mones-1986"/> Since 2002, molecular phylogenetic studies have recognized a close relationship between \'\'Hydrochoerus\'\' and \'\'[[Kerodon]]\'\', the rock cavies,<ref name="Rowe-2002"/> supporting placement of both genera in a subfamily of [[Caviidae]].<ref name=msw3/>\n\nPaleontological classifications previously used Hydrochoeridae for all capybaras, while using Hydrochoerinae for the living genus and its closest fossil relatives, such as \'\'[[Neochoerus]]\'\',<ref name="Vucetich-2005"/><ref name="Deschamps-2007"/> but more recently have adopted the classification of Hydrochoerinae within Caviidae.<ref name="Cerdeño-2019">{{cite journal|last1=Cerdeño |first1=E. |last2=Pérez |first2=M.E. |last3=Deschamps |first3=C.M. |last4=Contreras |first4=V.H. |year=2019 |title=A new capybara from the late Miocene of San Juan Province, Argentina, and its phylogenetic implications |journal=Acta Palaeontologica Polonica |volume=64 |issue=1 |pages=199–212 |doi=10.4202/app.00544.2018|doi-access=free |hdl=11336/117299 |hdl-access=free }}</ref> The taxonomy of fossil hydrochoerines is also in a state of flux. In recent years, the diversity of fossil hydrochoerines has been substantially reduced.<ref name="Vucetich-2005"/><ref name="Deschamps-2007"/> This is largely due to the recognition that capybara molar teeth show strong variation in shape over the life of an individual. In one instance, material referred to four genera and seven species on the basis of differences in molar shape was later thought to represent differently aged individuals of a single species, \'\'Cardiatherium paranense\'\'.<ref name="Vucetich-2005"/>\nAmong fossil species, the name "capybara" can refer to the many species of Hydrochoerinae that are more closely related to the modern \'\'Hydrochoerus\'\' than to the "cardiomyine" rodents like \'\'Cardiomys\'\'. The fossil genera \'\'Cardiatherium\'\', \'\'Phugatherium\'\', \'\'Hydrochoeropsis\'\', and \'\'Neochoerus\'\' are all capybaras under that concept.<ref name="Cerdeño-2019" />\n\n==Description==\n[[File:Hydrochoeris hydrochaeris in Brazil in Petrópolis, Rio de Janeiro, Brazil 09.jpg|left|thumb|Capybara in [[Petrópolis]], Brazil]]\nThe capybara has a heavy, barrel-shaped body and short head, with reddish-brown fur on the upper part of its body that turns yellowish-brown underneath. Its sweat glands can be found in the surface of the hairy portions of its skin, an unusual trait among rodents.<ref name="Mones-1986" /> The animal lacks [[Fur#Down hair|down hair]], and its [[Fur#Guard hair|guard hair]] differs little from over hair.<ref>{{Cite web|url=https://www.worldatlas.com/articles/10-delightful-facts-about-capybaras.html|title=The Cabybara – 10 Facts About the World\'s Largest Rodent|website=WorldAtlas|date=26 July 2019|language=en|access-date=2020-03-18}}</ref>[[File:Capybara skeleton.jpg|thumb|Skeleton of a capybara]]Adult capybaras grow to {{convert|106|to|134|cm|ft|abbr=on}} in length, stand {{convert|50|to|62|cm|in|abbr=on}} tall at the [[withers]], and typically weigh {{convert|35|to|66|kg|lb|abbr=on}}, with an average in the Venezuelan [[llanos]] of {{convert|48.9|kg|lb|abbr=on}}.<ref name=Arkive>[http://www.arkive.org/capybara/hydrochoerus-hydrochaeris/#text=Facts Capybara] {{Webarchive|url=https://web.archive.org/web/20120103075238/http://www.arkive.org/capybara/hydrochoerus-hydrochaeris/#text=Facts#text=Facts |date=2012-01-03 }}, Arkive</ref><ref name="Smithsonian"/><ref name="Palm Beach Zoo"/> Females are slightly heavier than males. The top recorded weights are {{convert|91|kg|lb|abbr=on}} for a wild female from Brazil and {{convert|73.5|kg|lb|abbr=on}} for a wild male from Uruguay.<ref name="Mones-1986"/><ref name="WAZA"/> Also, an 81&nbsp;kg individual was reported in São Paulo in 2001 or 2002.<ref>{{cite journal |last1=Ferraz |first1=Katia Maria Paschoaletto Micchi de Barros |last2=Bonach |first2=Kelly |last3=Verdade |first3=Luciano Martins |title=Relationship between body mass and body length in capybaras (\'\'Hydrochoerus hydrochaeris\'\') |journal=Biota Neotropica |date=2005 |volume=5 |issue=1 |pages=197–200 |doi=10.1590/S1676-06032005000100020 |doi-access=free }}</ref> The [[dental formula]] is {{DentalFormula|upper=1.0.1.3|lower=1.0.1.3}}. Capybaras have slightly [[Interdigital webbing|webbed]] feet and [[Vestigiality|vestigial]] tails.<ref name="Mones-1986"/> Their hind legs are slightly longer than their forelegs; they have three toes on their rear feet and four toes on their front feet.<ref name="enchantedlearning.com">{{cite web|url=http://www.enchantedlearning.com/subjects/mammals/rodent/Capybaraprintout.shtml |title=Capybara Printout |publisher=Enchantedlearning.com |access-date=2013-05-27}}</ref> Their muzzles are blunt, with nostrils, and the eyes and ears are near the top of their heads.\n\nIts [[karyotype]] has [[Diploid|2n]] = 66 and [[Fundamental number|FN]] = 102, meaning it has 66 chromosomes with a total of 102 arms.<ref name=msw3/><ref name="Mones-1986"/>\n\n==Ecology==\n[[File:055 Capybara swimming in Encontro das Águas State Park Photo by Giles Laurent.jpg|thumb|Capybara swimming in Encontro das Águas State Park, Brazil]]\n[[File:Yellow-headed caracara (Milvago chimachima) on capybara (Hydrochoeris hydrochaeris).JPG|left|thumb|[[Yellow-headed caracara]] on a capybara]]\nCapybaras are [[semiaquatic]] mammals<ref name="Palm Beach Zoo"/> found throughout all countries of South America except [[Chile]].<ref name="Bristol"/> They live in densely forested areas near bodies of water, such as lakes, rivers, swamps, ponds, and marshes,<ref name="Smithsonian"/> as well as flooded savannah and along rivers in the tropical rainforest. They are superb swimmers and can hold their breath underwater for up to five minutes at a time. Capybara have flourished in cattle ranches. They roam in home ranges averaging {{convert|10|ha|acre|abbr=off}} in high-density populations.<ref name="Mones-1986"/>\n\nMany escapees from captivity can also be found in similar watery habitats around the world. Sightings are fairly common in [[Florida]], although a breeding population has not yet been confirmed.<ref>{{cite web|url=http://myfwc.com/wildlifehabitats/nonnatives/mammals/capybara/|title=Nonnatives – Capybara|website=myfwc.com|access-date=2013-08-30|archive-date=2014-04-06|archive-url=https://web.archive.org/web/20140406221051/http://myfwc.com/wildlifehabitats/nonnatives/mammals/capybara/}}</ref> In 2011, one specimen was spotted on the [[Central Coast (California)|Central Coast of California]].<ref>{{cite news|url=http://www.latimes.com/news/local/la-me-0818-capybara-20110818,0,104462.story|title=A gnawing question answered: It\'s a capybara roaming Paso Robles|last=Mather|first=Kate|date=18 August 2011|work=[[Los Angeles Times]]|access-date=10 January 2012}}</ref> These escaped populations occur in areas where prehistoric capybaras inhabited; [[late Pleistocene]] capybaras inhabited Florida<ref>{{Cite journal|url=https://bioone.org/journals/proceedings-of-the-academy-of-natural-sciences-of-philadelphia/volume-167/issue-1/053.167.0105/A-Late-Pleistocene-capybara-Rodentia-Caviidae-Hydrochoerinae-from-near-Houston/10.1635/053.167.0105.short|doi=10.1635/053.167.0105|title=A Late Pleistocene capybara (Rodentia, Caviidae, Hydrochoerinae) from near Houston, Texas, USA, with a brief review of North American fossil capybaras|year=2020|last1=Baskin|first1=Jon|last2=Gervais|first2=P. Darrow|last3=Gervais|first3=Camille J.|journal=Proceedings of the Academy of Natural Sciences of Philadelphia|volume=167|issue=1 |page=57|bibcode=2020PANSP.167...57B |s2cid=216241471|url-access=subscription}}</ref> and \'\'[[Hydrochoerus hesperotiganites]]\'\' in [[California]] and \'\'[[Hydrochoerus gaylordi]]\'\' in [[Grenada]], and feral capybaras in North America may actually fill the ecological niche of the Pleistocene species.<ref>Erick J. Lundgren, Daniel Ramp, John Rowan, Owen Middleton, Simon D. Schowanek, Oscar Sanisidro, Scott P. Carroll, Matt Davis, Christopher J. Sandom, Jens-Christian Svenning, Arian D. Wallach, James A. Estes, 2020, \'\'[https://www.pnas.org/content/117/14/7871 Introduced herbivores restore Late Pleistocene ecological functions]\'\', PNAS, 117 (14), pp.7871-7878, [[Proceedings of the National Academy of Sciences of the United States of America]]</ref>\n\n===Diet and predation===\n[[File:Capybaras (Hydrochoerus hydrochaeris) grazing in the evening.jpg|thumb|Capybaras grazing]]\nCapybaras are [[herbivore]]s, grazing mainly on grasses and [[aquatic plants]],<ref name="Smithsonian"/><ref name="Forero-Montaña-2003"/> as well as fruit and tree bark.<ref name="Palm Beach Zoo"/> They are very selective feeders<ref name="Quintana-1998"/> and feed on the leaves of one species and disregard other species surrounding it. They eat a greater variety of plants during the dry season, as fewer plants are available. While they eat grass during the wet season, they have to switch to more abundant reeds during the dry season.<ref name="Barreto-1998"/> Plants that capybaras eat during the summer lose their nutritional value in the winter, so they are not consumed at that time.<ref name="Quintana-1998"/> The capybara\'s jaw hinge is not perpendicular, so they chew food by grinding back-and-forth rather than side-to-side.<ref name="SFZoo"/> Capybaras are [[coprophagous|autocoprophagous]],<ref name="taronga-zoo"/> meaning they eat their own feces as a source of bacterial [[gut flora]], to help digest the [[cellulose]] in the grass that forms their normal diet, and to extract the maximum protein and vitamins from their food. They also regurgitate food to masticate again, similar to cud-chewing by cattle.<ref name="taronga-zoo">{{cite web |title=Meet Taronga\'s Capybaras |url=https://taronga.org.au/sydney-zoo/must-see/capybaras |website=Taronga Zoo |access-date=29 December 2021 |ref=taronga-zoo}}</ref><ref name="Lord-1994"/> Like other rodents, a capybara\'s front teeth grow continually to compensate for the constant wear from eating grasses;<ref name="Bristol"/> their cheek teeth also grow continuously.<ref name="SFZoo"/>\n[[File:Parque estadual encontro das aguas - Gustavo Gaspari 03, auto white balance i.jpg|left|thumb|A [[jaguar]] hunting two juvenile capybaras]]\nLike its relative the guinea pig, the capybara does not have the capacity to synthesize [[vitamin C]], and capybaras not supplemented with vitamin C in captivity have been reported to develop [[Periodontal disease|gum disease]] as a sign of [[scurvy]].<ref name="Cueto-2000"/>\n\nThe maximum lifespan of the capybara is 8 to 10 years,<ref name="Burton-2002"/> but in the wild capybaras usually do not live longer than four years because of predation from South American cats such as [[jaguar]]s, [[ocelot]]s and [[cougar]]s and from non-mammalian predators such as [[eagle]]s, [[caiman]]s and [[Eunectes murinus|green anaconda]]s.<ref name="Bristol"/><ref name="SoundsandColours"/>\n\n==Social organization==\n[[File:Hydrochoerus hydrochaeris 222765566.jpg|thumb|Trio of capybaras in [[El Palmar National Park]], Argentina]]\n[[File:Capybara (Hydrochoerus hydrochaeris) alpha male.JPG|thumb|Male capybara with a visible morrillo on the snout]]\n\nCapybaras are [[gregarious]]. While they sometimes live solitarily, they are more commonly found in groups of around 10–20 individuals, with two to four adult males, four to seven adult females, and the remainder juveniles.<ref name="Alho-1987"/> Capybara groups can consist of as many as 50 or 100 individuals during the dry season<ref name="Lord-1994"/><ref name="Macdonald-1981"/> when the animals gather around available water sources. Males establish social bonds, dominance, or general group consensus.<ref name="Macdonald-1981"/> They can make dog-like barks<ref name="Lord-1994"/> when threatened or when females are herding young.<ref name="Murphey-1985"/>\n\nCapybaras have two types of [[scent gland]]s: a morrillo, located on the snout, and [[anal gland]]s. Both sexes have these glands, but males have much larger morrillos and use their anal glands more frequently. The anal glands of males are also lined with detachable hairs. A crystalline form of scent secretion is coated on these hairs and is released when in contact with objects such as plants. These hairs have a longer-lasting scent mark and are tasted by other capybaras. Capybaras scent-mark by rubbing their morrillos on objects, or by walking over scrub and marking it with their anal glands. Capybaras can spread their scent farther by urinating; however, females usually mark without urinating and scent-mark less frequently than males overall. Females mark more often during the wet season when they are in [[estrus]]. In addition to objects, males also scent-mark females.<ref name="Macdonald-1984"/>\n\n===Reproduction===\n[[File:Capivara(Hydrochoerus hydrochaeris).jpg|thumb|left|Mother with litter of pups]]\nWhen in [[estrus]], the female\'s scent changes subtly and nearby males begin pursuit.<ref name="Herrera-1993">{{cite journal|doi=10.1093/beheco/4.2.114|title= Aggression, dominance, and mating success among capybara males (\'\'Hydrochaeris hypdrochaeris\'\')|year=1993|last1=Herrera|first1=Emilio A.|last2=MacDonald|first2=David W.|journal=[[Behavioral Ecology (journal)|Behavioral Ecology]]|volume=4|issue=2|page=114}}</ref> In addition, a female alerts males she is in estrus by whistling through her nose.<ref name="Lord-1994"/> During mating, the female has the advantage and mating choice. Capybaras mate only in water, and if a female does not want to mate with a certain male, she either submerges or leaves the water.<ref name="Lord-1994"/><ref name="Macdonald-1981"/> Dominant males are highly protective of the females, but they usually cannot prevent some of the subordinates from copulating. The larger the group, the harder it is for the male to watch all the females. Dominant males secure significantly more matings than each subordinate, but subordinate males, as a class, are responsible for more matings than each dominant male.<ref name="Herrera-1993"/> The lifespan of the capybara\'s sperm is longer than that of other rodents.<ref name="Paula-1999"/> Capybara [[gestation]] is 130–150 days, and produces a litter of four young on average, but may produce between one and eight in a single litter.<ref name="Mones-1986"/> Birth is on land and the female rejoins the group within a few hours of delivering the newborn capybaras, which join the group as soon as they are mobile. Within a week, the young can eat grass, but continue to suckle—from any female in the group—until weaned around 16 weeks. The young form a group within the main group.<ref name="Bristol"/> [[Alloparenting]] has been observed in this species.<ref name="Macdonald-1981"/> Breeding peaks between April and May in Venezuela and between October and November in [[Mato Grosso]], Brazil.<ref name="Mones-1986"/>\n\n===Activities===\nThough quite agile on land, capybaras are equally at home in the water. They are excellent swimmers, and can remain completely submerged for up to five minutes,<ref name="Smithsonian"/> an ability they use to evade predators. Capybaras can sleep in water, keeping only their noses out. As temperatures increase during the day, they wallow in water and then graze during the late afternoon and early evening.<ref name="Mones-1986"/> They also spend time wallowing in mud.<ref name="enchantedlearning.com"/> They rest around midnight and then continue to graze before dawn.<ref name="Mones-1986" />\n\n===Communication===\nCapybaras communicate using barks, chirps, whistles, huffs, and purrs.<ref>{{cite web | url=https://zoo.sandiegozoo.org/animals/capybara | title=Capybara }}</ref>\n\n[[File:Capybara Ueno Zoo 2009.ogv|thumb|Capybaras in captivity, 2009]]\n\n==Conservation and human interaction==\nCapybaras are not considered a threatened species;<ref name="iucn" /> their population is stable throughout most of their South American range, though in some areas hunting has reduced their numbers.<ref name="Smithsonian"/><ref name="Bristol"/> Capybaras are hunted for their meat and pelts in some areas,<ref name="Thompson-2008" /> and otherwise killed by humans who see their grazing as competition for livestock. In some areas, they are farmed, which has the effect of ensuring the wetland habitats are protected. Their survival is aided by their ability to breed rapidly.<ref name="Bristol" />\n[[File:Hydrochoerus hydrochaeris (54906494753).jpg|thumb|Captive capybara at [[Copenhagen Zoo]], Denmark, in 2025]]\nCapybaras have adapted well to urbanization in South America. They can be found in many areas in zoos and parks,<ref name="SFZoo" /> and may live for 12 years in captivity, more than double their wild lifespan.<ref name="Bristol" /> Capybaras are docile and usually allow humans to pet and hand-feed them, but physical contact is normally discouraged, as their [[tick]]s can be [[vector (epidemiology)|vectors]] to [[Rocky Mountain spotted fever]].<ref>{{cite web|url=http://drauziovarella.com.br/audios-videos/estacao-medicina/febre-maculosa/ |title=Febre maculosa: "Os médicos no Brasil não conhecem a doença|date=12 April 2011|trans-title= Rocky Mountain spotted fever: Brazilian doctors unaware of the disease |language=pt |publisher=drauziovarella.com.br |access-date=2015-08-13}}</ref> The [[European Association of Zoos and Aquaria]] asked [[Drusillas Park]] in [[Alfriston]], [[Sussex]], England, to keep the [[studbook]] for capybaras, to monitor captive populations in Europe. The studbook includes information about all births, deaths and movements of capybaras, as well as how they are related.<ref>{{cite web|url=http://www.drusillas.co.uk/conservation-1 |title=Conservation at Drusillas Park |publisher=Drusillas.co.uk |access-date=2013-05-27}}</ref>\n\nCapybaras are farmed for meat and skins in South America.<ref name="SDzoo"/> The meat is considered unsuitable to eat in some areas, while in other areas it is considered an important source of protein.<ref name="Mones-1986"/> In parts of South America, especially in Venezuela, capybara meat is popular during [[Lent]] and [[Holy Week]] as the Catholic Church (according to a legend) previously issued special dispensation to allow it to be eaten while other meats are [[Fasting and abstinence in the Catholic Church|generally forbidden]].<ref name="Ellsworth"/><ref name="Romero-2007">{{Cite news |last=Romero |first=Simon |date=2007-03-21 |title=In Venezuela, Rodents Can Be a Delicacy |url=https://www.nytimes.com/2007/03/21/world/americas/21rodent.html |access-date=2021-04-27 |work=The New York Times |language=en-US |issn=0362-4331 |quote=Legend has it that eating capybara, known here as chigüire (pronounced chee-GWEE-reh), got a boost in the 18th century when the local clergy asked the Vatican to give capybara the status of fish. (...) It remains more popular in Venezuela\'s rural interior than in the capital.}}</ref>{{New archival link needed|date=April 2026}} There is widespread perception in Venezuela that consumption of capybaras is exclusive to rural people.<ref name="Romero-2007"/>\n\nBrazilian Lyme-like [[borreliosis]] likely involves capybaras as reservoirs and \'\'[[Amblyomma]]\'\' and \'\'[[Rhipicephalus]]\'\' ticks as vectors.<ref>{{cite journal |last1=Basile |first1=Roberta Carvalho |last2=Yoshinari |first2=Natalino Hajime |last3=Mantovani |first3=Elenice |last4=Bonoldi |first4=Virgínia Nazário |last5=Macoris |first5=Delphim da Graça |last6=Queiroz-Neto |first6=Antonio de |title=Brazilian borreliosis with special emphasis on humans and horses |journal=Brazilian Journal of Microbiology |date=4 October 2016 |volume=48 |issue=1 |pages=167–172 |doi=10.1016/j.bjm.2016.09.005 |pmid=27769883 |pmc=5220628 }}</ref>\n\nA [[Animal cafe#Capybara café|capybara café]] in [[St. Augustine, Florida|St. Augustine]], [[Florida]] allows visitors to interact with and give head scratches to the rodents.<ref>{{cite news|title=Giant rodents cuddle with visitors at the Capybara Cafe in Florida|url=https://apnews.com/article/florida-capybara-cafe-st-augustine-54ce3807f084e9de61f72a79c6633e10|newspaper=Associated Press News|date=April 12, 2025}}</ref>\n\n== In popular culture ==\nCapybaras have amassed [[Fandom|fandoms]] in [[Japan]] and [[China]], particularly among youth. This has been attributed to their perception as role models of emotional well-being and harmoniousness.<ref name=":0">{{Cite news |date=14 Sep 2024 |title=How the humble capybara became a spirit animal for Asia\'s youth |url=https://www.abc.net.au/news/2024-09-14/how-capybaras-became-asia-s-spirit-animal/104335784 |work=[[ABC_News_(Australia)|ABC News (Australia)]]}}</ref> In Japan, [[Izu Shaboten Zoo]] and other zoos provide [[onsen|hot spring baths]] for capybaras. Video clips of the bathing capybaras have millions of views.<ref name="Murakami-2020">{{cite web|url=https://www.reuters.com/article/us-olympics-2020-capybara-idCAKBN1ZY0FY|title=Olympics and Year of the Rat give starring role to Japan\'s capybaras|website=[[Reuters]]|first=Sakura|last=Murakami|date=4 February 2020|access-date=23 October 2021}}</ref> These capybaras spawned a series of merchandise such as [[plush toy]]s, and provided inspiration for the [[anime]] character \'\'Kapibara-san.\'\'<ref>{{cite web|url=https://qz.com/986398/how-the-capybara-the-worlds-largest-rodent-became-a-superstar-in-japan/|title=How the world\'s largest rodent became a superstar in Japan|website=[[Quartz (publication)|Quartz]]|first=Isabella|last=Steger|date=19 May 2017|access-date=23 October 2021}}</ref> \n\nCapybaras have become a figure in [[Internet meme|meme culture]] in the 2020s.<ref name="Mouriquand-2023">{{cite news |last1=Mouriquand |first1=David |title=Why are capybaras systematically taking over social media? |url=https://www.euronews.com/culture/2023/04/12/why-are-capybaras-systematically-taking-over-social-media |access-date=24 February 2025 |work=Euro News |date=December 4, 2023}}</ref> Common meme formats pair capybaras with the song "[[After Party (song)|After Party]]" by [[Don Toliver]].<ref>{{Cite web |last=Lopez |first=Sophia |date=2022-08-01 |title=Capybaras are taking over the internet |url=https://thegauntlet.ca/2022/08/01/capybaras-are-taking-over-the-internet/ |access-date=2022-09-02 |website=The Gauntlet |language=en-US}}</ref> A song about capybaras was released and became highly popular on [[TikTok]] in 2022.<ref>{{Cite web|title=Capybara Song / Капибара|url=https://knowyourmeme.com/memes/capybara-song-%D0%BA%D0%B0%D0%BF%D0%B8%D0%B1%D0%B0%D1%80%D0%B0|website=Know Your Meme|date=2023-03-13|access-date=2025-11-29|language=en}}</ref> Capybaras have gained a reputation as a symbol of calm due to their perceived "unflappability",<ref>{{cite web |title=What has webbed feet, a big snout and is adored on the internet? |url=https://www.economist.com/culture/2025/11/25/what-has-webbed-feet-a-big-snout-and-is-adored-on-the-internet |publisher=The Economist |access-date=14 January 2026}}</ref> and their personalities have been described as "[[The Buddha|buddha]]-like".<ref name=":0" />\n\nIn August 2021, Argentine and international media reported that capybaras had been disrupting life in [[Nordelta]], an affluent gated community north of [[Buenos Aires]] built atop the local capybara\'s preexisting wetland habitat. This inspired social media users to jokingly adopt the capybara as a symbol of [[class struggle]] and [[communism]].<ref name="Goñi-2021">{{cite web|title=Attack of the giant rodents or class war? Argentina\'s rich riled by new neighbors|newspaper=[[The Guardian]] |date=22 August 2021 |url=https://www.theguardian.com/world/2021/aug/22/argentina-capybaras-giant-rodents-gated-community |last=Goñi |first=Uki}}</ref>\n\n==See also==\n* \'\'[[Josephoartigasia monesi]]\'\', an extinct species identified as the largest known rodent ever\n* [[Kurloff cell]], a type of cell found in capybaras and guinea pigs\n* \'\'[[Capybara Walking]]\'\', a historical animal locomotion film by [[Eadweard Muybridge]]\n\n==Notes==\n<references group="note" />\n{{notelist}}\n\n==References==\n{{Reflist|refs=\n<ref name="Bristol">[http://www.bristolzoo.org.uk/learning/animals/mammals/capybara Bristol Zoo Gardens (UK) \'\'Capybara\'\'] {{webarchive|url=https://web.archive.org/web/20070918183854/http://www.bristolzoo.org.uk/learning/animals/mammals/capybara |date=2007-09-18 }}. Bristolzoo.org.uk. Retrieved on 2011-12-07.</ref>\n<ref name="Barreto-1998">{{cite journal |title=Foraging patterns of capybaras in a seasonally flooded savanna of Venezuela| jstor=2559868|doi=10.1017/S0266467498000078 |year=1998 |last1=Barreto |first1=Guillermo R. |last2=Herrera |first2=Emilio A. |journal=Journal of Tropical Ecology |volume=14 | issue=1| pages=87–98| s2cid=84982123}}</ref>\n<ref name="Quintana-1998">{{cite journal |last1=Quintana |first1=R.D. |last2=Monge |first2=S. |last3=Malvárez |first3=A.I. |title=Feeding patterns of capybara \'\'Hydrochaeris hydrochaeris\'\' (Rodentia, Hydrochaeridae) and cattle in the non-insular area of the Lower Delta of the Paraná River, Argentina |journal=Mammalia |date=1998 |volume=62 |issue=1 |pages=37–52 |doi=10.1515/mamm.1998.62.1.37 |s2cid=83976640 }}</ref>\n<ref name="Burton-2002">Burton M and Burton R. (2002) \'\'The International Wildlife Encyclopedia\'\'. Marshall Cavendish, {{ISBN|0-7614-7269-X}}, p. 384</ref>\n<ref name="SoundsandColours">[http://soundsandcolours.com/subjects/south-american-nature/capybara-the-master-of-the-grasses-pest-or-prey-3937/ Capybara, the master of the grasses: pest or prey]  Sounds and Colours. Retrieved on 23 January 2011.</ref>\n<ref name="SFZoo">[https://web.archive.org/web/20070614005832/http://www.sfzoo.org/cgi-bin/animals.py?ID=90 Capybara. \'\'Hydrochaeris hydrochaeris\'\']. San Francisco Zoo</ref>\n<ref name="SDzoo">{{cite web  | date = October 2008  | publisher = San Diego Zoo  | title = Capybara, \'\'Hydrochoerus hydrochaeris\'\'  | url = http://library.sandiegozoo.org/factsheets/capybara/capybara.htm  | access-date = 22 June 2011  | archive-url = https://web.archive.org/web/20110930051431/http://library.sandiegozoo.org/factsheets/capybara/capybara.htm  | archive-date = 30 September 2011  }}</ref>\n<ref name="Alho-1987">{{cite journal |last1=Alho |first1=Cleber J.R. |last2=Rondon |first2=Nelson L. |title=Habitats, population densities, and social structure of capybaras (\'\'Hydrochaeris Hydrochaeris\'\', Rodentia) in the Pantanal, Brazil |journal=[[Revista Brasileira de Zoologia]] |date=1987 |volume=4 |issue=2 |pages=139–149 |doi=10.1590/s0101-81751987000200006 |doi-access=free }}</ref>\n<ref name="Lord-1994">{{cite journal |last1=Lord |first1=Rexford D. |title=A descriptive account of capybara behaviour |journal=Studies on Neotropical Fauna and Environment |date=March 1994 |volume=29 |issue=1 |pages=11–22 |doi=10.1080/01650529409360912 |bibcode=1994SNFE...29...11L }}</ref>\n<ref name="Macdonald-1981">{{cite journal |last1=Macdonald |first1=D. W. |title=Dwindling resources and the social behaviour of Capybaras, (\'\'Hydrochoerus hydrochaeris\'\') (Mammalia) |journal=Journal of Zoology |date=July 1981 |volume=194 |issue=3 |pages=371–391 |doi=10.1111/j.1469-7998.1981.tb04588.x |bibcode=1981JZoo..194..371M }}</ref>\n<ref name="Murphey-1985">{{cite journal |last1=Murphey |first1=Robert M. |last2=Mariano |first2=Jorge S. |last3=Moura Duarte |first3=Francisco A. |title=Behavioral observations in a capybara colony (\'\'Hydrochoerus hydrochaeris\'\') |journal=Applied Animal Behaviour Science |date=May 1985 |volume=14 |issue=1 |pages=89–98 |doi=10.1016/0168-1591(85)90040-1 }}</ref>\n<ref name="Paula-1999">{{cite journal |last1=Paula |first1=T.A.R. |last2=Chiarini-Garcia |first2=H. |last3=França |first3=L.R. |title=Seminiferous epithelium cycle and its duration in capybaras (Hydrochoerus hydrochaeris) |journal=Tissue and Cell |date=June 1999 |volume=31 |issue=3 |pages=327–334 |doi=10.1054/tice.1999.0039 |pmid=10481304 }}</ref>\n<ref name="Cueto-2000">{{cite journal |last1=Cueto |first1=Gerardo Ruben |last2=Allekotte |first2=Roman |last3=Kravetz |first3=Fernando Osvaldo |title=Scurvy in capybaras bred in captivity in Argentine |journal=Journal of Wildlife Diseases |date=January 2000 |volume=36 |issue=1 |pages=97–101 |doi=10.7589/0090-3558-36.1.97 |pmid=10682750 |s2cid=6491859 |doi-access=free }}</ref>\n<ref name="WAZA">[http://www.waza.org/virtualzoo/factsheet.php?id=110-020-001-001&view=Rodents%20and%20Hares&main=virtualzoo World Association of Zoos and Aquariums]. [[World Association of Zoos and Aquariums|WAZA]]. Retrieved on 2011-12-07.</ref>\n<ref name="Mones-1986">{{cite journal |last1=Mones |first1=Alvaro |last2=Ojasti |first2=Juhani |title=Hydrochoerus hydrochaeris |journal=Mammalian Species |date=16 June 1986 |issue=264 |pages=1–7 |doi=10.2307/3503784 |jstor=3503784 |bibcode=1986MamSp.264....1M |s2cid=250991487 |doi-access=free }}</ref>\n<ref name="Smithsonian">[https://web.archive.org/web/20050930231549/http://nationalzoo.si.edu/Animals/Amazonia/Facts/capybarafacts.cfm Capybara Facts.] [[Smithsonian National Zoological Park]]. Retrieved on 16 December 2007.</ref>\n<ref name="Palm Beach Zoo">[https://web.archive.org/web/20100620162726/http://palmbeachzoo.org/animals/capybara.html Capybara.] Palm Beach Zoo. Retrieved on 17 December 2007.</ref>\n<ref name="Macdonald-1984">{{cite journal |last1=Macdonald |first1=D. W. |last2=Krantz |first2=K. |last3=Aplin |first3=R. T. |title=Behavioral anatomical and chemical aspects of scent marking among Capybaras (\'\'Hydrochaeris hypdrochaeris\'\') (Rodentia: Caviomorpha) |journal=Journal of Zoology |date=March 1984 |volume=202 |issue=3 |pages=341–360 |doi=10.1111/j.1469-7998.1984.tb05087.x }}</ref>\n<ref name="Forero-Montaña-2003">{{cite journal |last1=Forero-Montaña |first1=Jimena |last2=Betancur |first2=Julio |last3=Cavelier |first3=Jaime |title=Dieta del capibara \'\'Hydrochaeris hydrochaeris\'\' (Rodentia: Hydrochaeridae) en Caño Limón, Arauca, Colombia |trans-title=Distribution and abundance of Caiman crocodilus in the Caño Negro National Wild Life Refuge, Costa Rica |language=es |journal=[[Revista de Biología Tropical]] |date=June 2003 |volume=51 |issue=2 |pages=571–578 |url=https://www.scielo.sa.cr/scielo.php?script=sci_arttext&pid=S0034-77442003000200029 |pmid=15162749 }}</ref><ref name="Ellsworth">Ellsworth, Brian (24 March 2005). [http://www.nysun.com/article/11063 "In Days Before Easter, Venezuelans Tuck Into Rodent-Related Delicacy"] {{Webarchive|url=https://web.archive.org/web/20080705215536/http://www.nysun.com/article/11063 |date=5 July 2008 }}. \'\'[[New York Sun]]\'\'.</ref>\n<ref name="Thompson-2008">Thompson, Andy (18 January 2008) [https://archive.today/20130204101346/http://www2.timesdispatch.com/lifestyles/2008/jan/18/-rtd_2008_01_18_0043-ar-147752/ Trip to South America gives new meaning to outdoors life]. Richmond Times.</ref>\n<ref name="Rowe-2002">{{cite journal |last1=Rowe |first1=Diane L. |last2=Honeycutt |first2=Rodney L. |title=Phylogenetic Relationships, Ecological Correlates, and Molecular Evolution Within the Cavioidea (Mammalia, Rodentia) |journal=Molecular Biology and Evolution |date=March 2002 |volume=19 |issue=3 |pages=263–277 |doi=10.1093/oxfordjournals.molbev.a004080 |pmid=11861886 |doi-access=free }}</ref>\n<ref name="Vucetich-2005">{{cite journal |last1=Vucetich |first1=María G. |last2=Deschamps |first2=Cecilia M. |last3=Olivares |first3=Itatí |last4=Dozo |first4=María T. |title=Capybaras, size, shape, and time: A model kit |journal=Acta Palaeontologica Polonica |volume=50 |issue=2 |year=2005 |pages=259–272 |url=https://www.app.pan.pl/article/item/app50-259.html }}</ref>\n<ref name="Deschamps-2007">{{cite journal |last1=Deschamps |first1=Cecilia M. |last2=Olivares |first2=Itatí |last3=Vieytes |first3=Emma Carolina |last4=Vucetich |first4=María Guiomar |title=Ontogeny and diversity of the oldest capybaras (Rodentia: Hydrochoeridae; late Miocene of Argentina) |journal=Journal of Vertebrate Paleontology |date=12 September 2007 |volume=27 |issue=3 |pages=683–692 |doi=10.1671/0272-4634(2007)27[683:oadoto]2.0.co;2 |jstor=30126368 |s2cid=86217854 }}</ref>\n}}\n\n==External links==\n{{EB1911 poster|Capybara}}\n* {{Commons category-inline|Hydrochoerus hydrochaeris|Capybaras}}\n{{Portal-bar|Mammals|South America}}\n\n{{Caviidae nav}}\n{{Taxonbar|from=Q131538}}\n\n[[Category:Mammals described in 1766]]\n[[Category:Cavies]]\n[[Category:Herbivorous mammals]]\n[[Category:Mammals of Argentina]]\n[[Category:Mammals of Bolivia]]\n[[Category:Rodents of Brazil]]\n[[Category:Mammals of Colombia]]\n[[Category:Mammals of Ecuador]]\n[[Category:Mammals of French Guiana]]\n[[Category:Mammals of Guyana]]\n[[Category:Mammals of Paraguay]]\n[[Category:Mammals of Peru]]\n[[Category:Mammals of Uruguay]]\n[[Category:Mammals of Venezuela]]\n[[Category:Articles containing video clips]]\n[[Category:Semiaquatic mammals]]\n[[Category:Animal taxa named by Carl Linnaeus]]\n[[Category:Internet memes introduced in the 2020s]]', tool_call_id='call_tnGby2t392oBFuIWvFp1Nv9o', timestamp=datetime.datetime(2026, 5, 4, 22, 17, 46, 227886, tzinfo=datetime.timezone.utc))], timestamp=datetime.datetime(2026, 5, 4, 22, 17, 46, 229019, tzinfo=datetime.timezone.utc), run_id='019df511-941d-75de-9f54-6544f1917fbc', conversation_id='019df511-941d-75de-9f54-654395292aa2')
--------------------------------------------------
ModelResponse(parts=[TextPart(content='The main threats to capybara populations include:\n\n1. Hunting: Capybaras are hunted for their meat and hide in some areas. Hunting has reduced their numbers in certain regions.\n2. Competition and Human Conflict: They are sometimes killed by humans who see their grazing as competition for livestock.\n3. Habitat Disturbance: Urbanization and habitat destruction can disrupt their natural wetland habitats, although capybaras have shown some adaptation to urban environments.\n\nDespite these threats, capybaras are not currently considered a threatened species, and their population is generally stable throughout most of their South American range. Their ability to breed rapidly also aids their survival. In some places, capybaras are farmed, which helps protect their wetland habitats.')], usage=RequestUsage(input_tokens=11091, output_tokens=154, details={'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}), model_name='gpt-4.1-mini-2025-04-14', timestamp=datetime.datetime(2026, 5, 4, 22, 17, 48, 460739, tzinfo=datetime.timezone.utc), provider_name='openai', provider_url='https://api.openai.com/v1/', provider_details={'finish_reason': 'stop', 'timestamp': datetime.datetime(2026, 5, 4, 22, 17, 46, tzinfo=TzInfo(0))}, provider_response_id='chatcmpl-DbvtiCtccSmjy5H95YD1OEhwoZ0lb', finish_reason='stop', run_id='019df511-941d-75de-9f54-6544f1917fbc', conversation_id='019df511-941d-75de-9f54-654395292aa2')
--------------------------------------------------
```

#### Answer - 
Tools used:
search_wikipedia → get_page → search_wikipedia → get_page

Total tool calls: 4

Final answer:
The main threats to capybara populations include hunting, human-wildlife conflict due to grazing competition, and habitat disturbance from urbanization and wetland destruction. Despite these threats, capybaras are not currently considered threatened and maintain stable populations across most of their range due to high reproductive rates and adaptability.

#### Explaination

agent made the following tool calls:

- search_wikipedia → query: "capybara threats"
- get_page → page: "Capybara"
- search_wikipedia → query: "capybara threats" (second refinement attempt by model)
- get_page → page: "Capybara" (again reused same page)