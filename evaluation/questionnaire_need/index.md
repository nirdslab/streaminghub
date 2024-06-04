<form action="/survey/submit" method="POST">

# StreamingHub Questionnaire - Introduction

The text below describes the perspectives of three researchers; **Alice**, **Bob**, and **Cindy**.

![Personas](https://raw.githubusercontent.com/nirdslab/streaminghub/master/evaluation/questionnaire_need/assets/personas.png)

1. **Alice (Dataset Curation) -** Collecting and organizing datasets for easy reuse
2. **Bob (Algorithm Design) -** Developing RT algorithms and validating them on existing data
3. **Cindy (Improving Productivity) -** Enabling seamless integration of datasets and algorithms

## 👩🏽‍🎓 Alice (Dataset Curation)

**Alice** recently recorded eye movement data of **10** participants through a user study. In the study, the participants performed **10** different tasks, each under **3** different conditions, totaling **30** recordings per participant.

```bash
ADHD_SIN/
├── 001_01_1.csv
├── 001_01_2.csv
├── 001_01_3.csv
├ ....
├── 001_10_1.csv
├── 001_10_2.csv
├── 001_10_3.csv
├ ....
├── 010_10_1.csv
├── 010_10_2.csv
├── 010_10_3.csv

(300 files total)
```

All recordings were stored in CSV format, and named as `XXX_YY_Z.csv`, where `XXX`, `YY`, and `Z` represent the following.

| Pattern | Experiment Variable | Allowed Values |
| ------- | ------------------- | -------------- |
| XXX     | participant_id      | 001 to 010     |
| YY      | task_id             | 01 to 10       |
| Z       | condition_id        | 1 to 3         |

Each `XXX_YY_Z.csv` file contains time-series data in tabular format.

## 👨🏽‍🎓 Bob (Algorithm Design)

**Bob** is developing an algorithm to processes eye movement data streams in real-time. The algorithm resides in a file named `impl.py`, which looks as follows:

```python
class RTAlgorithm:
	_output: float
	# algorithm logic
	...

	def step(self, t: float, x: float, y: float, d: float) -> float:
		# run algorithm and update self._output
		...
		# return output
		return self._output
```

To run the algorithm, **Bob** first creates an instance of `RTAlgorithm` and then calls the `step()` function on each measurement **sequentially**. Each `step()` call returns a scalar-valued output computed over all inputs the `RTAlgorithm` instance has seen so far.

## 👩🏽‍💼 Cindy (Improving Productivity)

**Cindy** notices that her students put a considerable effort to connect existing datasets with RT algorithms. To improve productivity, she is looking for a solution that works across all/most use cases of her students and collaborators.

<hr>

# Scenario A - Dataset Curation

> 💡 **Alice wants to make her dataset reusable for others.**

<hr>

## Question A1

> 💡 Alice decides to create a README to answer any questions Bob may get. Based on her past experiences, she tries to cover 4 common questions in the README.
>
> (a) **what experimental variables exist** (i.e., `participant_id`, `task_id`, `condition_id`),<br>
> (b) **what variables each file represents** (i.e., `XXX_YY_Z.csv`),<br>
> (c) **what measurements each column represents** (e.g. time in `timestamp_ms` column),<br>
> (d) **units/scale of each measurement** (e.g., time in `ms` scale).<br>
>
> When sharing the dataset, Alice asks Bob to first go through the README, find the files/columns needed for his RT algorithm, and scale their values into the algorithm’s target range before calling `step()`.

Based on your experience, please rate how **difficult** and **time-consuming** you think the process of **covering each aspect through documentation** could get.

> **Scale: 1 = Very Low; 2 = Low; 3 = Neutral; 4 = High; 5 = Very High**

| Criteria                                                   | Task Difficulty       | Time Demand           |
| ---------------------------------------------------------- | --------------------- | --------------------- |
| Documenting What Experimental Variables Exist              | <input name="a1_1_d"> | <input name="a1_1_t"> |
| Documenting What Variables Each File Represents            | <input name="a1_2_d"> | <input name="a1_2_t"> |
| Documenting What Measurements Each Column/Field Represents | <input name="a1_3_d"> | <input name="a1_3_t"> |
| Documenting What Units / Scale Each Measurement is in      | <input name="a1_4_d"> | <input name="a1_4_t"> |

<hr>

## Question A2

Based on your experience, please rate how **difficult** and **time-consuming** you think the process of **Bob transforming the dataset into target format** could get, under each condition.

> **Level of Communication**
>
> - **Good -** Alice is willing to answer any questions Bob might have
> - **Poor -** Alice doesn’t have time to answer any questions Bob might have
>
> **File Format of Data**
>
> - **Open -** Alice saved data in a open filetype (CSV). Bob can view them without paid software.
> - **Closed -** Alice saved data in a closed filetype (EDF) from the recording software. Bob needs paid software to view them.

> **Scale: 1 = Very Low; 2 = Low; 3 = Neutral; 4 = High; 5 = Very High**

| Comms | Filetype | Task Difficulty       | Time Demand           |
| ----- | -------- | --------------------- | --------------------- |
| Good  | Open     | <input name="a2_1_d"> | <input name="a2_1_t"> |
| Good  | Closed   | <input name="a2_2_d"> | <input name="a2_2_t"> |
| Poor  | Open     | <input name="a2_3_d"> | <input name="a2_3_t"> |
| Poor  | Closed   | <input name="a2_4_d"> | <input name="a2_4_t"> |

<hr>

## Question A3

> 💡 Being a helpful colleague, Alice decides to transform data into the format Bob needs, and share that version instead.
>
> Bob mentions that his algorithm expects 4 values (`t`, `x`, `y`, `d`) representing the timestamp (`t`) in seconds, gaze position (`x`, `y`) in range `[0,1]`, and pupil diameter (`d`) in mm. However, Alice has saved the data under different names and units (e.g. `t` is named `timestamp_ns`, and is in `ms` scale). To avoid any confusion, she decides to transform the data herself, and share that version instead.

Based on your experience, please rate how **difficult** and **time-consuming** you think the process of **ALICE transforming the dataset into target format** could get, under each condition.

> **Level of Communication**
>
> - **Good -** Bob is willing to answer any questions Alice might have
> - **Poor -** Bob doesn’t have time to answer any questions Alice might have
>
> **Format of Data Files**
>
> - **Open -** Alice saved data in a open filetype (CSV). She can view them without paid software.
> - **Closed -** Alice saved data in a closed filetype (EDF) from the recording software. She needs paid software to view them.

> **Scale: 1 = Very Low; 2 = Low; 3 = Neutral; 4 = High; 5 = Very High**

| Comms | Filetype | Task Difficulty       | Time Demand           |
| ----- | -------- | --------------------- | --------------------- |
| Good  | Open     | <input name="a3_1_d"> | <input name="a3_1_t"> |
| Good  | Closed   | <input name="a3_2_d"> | <input name="a3_2_t"> |
| Poor  | Open     | <input name="a3_3_d"> | <input name="a3_3_t"> |
| Poor  | Closed   | <input name="a3_4_d"> | <input name="a3_4_t"> |

<hr>

## Question A4

**Alice** notices that in the past, when sharing user-study datasets, the recipients had similar questions about loading data. This time, to save herself and Bob time, she created a script named `dataloader.py` to load the data and shared this with Bob. The script looks as follows:

```python
import pandas as pd

dataset_dir = "/path/to/dataset"

def load_data(
	participant_id: str,
	task_id: str,
	condition_id: str,
	columns: list[str]
) -> pd.DataFrame:
	# file names have the pattern XXX_YY_Z.csv
	file_name = f"{dataset_dir}/{participant_id}_{task_id}_{condition_id}.csv"
	# load the recording
	df = pd.read_csv(file_name).set_index("timestamp_ms").sort_index()
	# return requested columns
	return df[columns]
```

To use `dataloader.py`, Alice instructs Bob to identify the columns needed for his RT algorithm, and pass them as the `columns` argument when calling `load_data()`.

Based on your experience, please rate the processes of **Bob reusing existing data loading code** and **Bob manually writing data loading code** in terms of **task difficulty** and **time demand**.

> **Scale: 1 = Very Low; 2 = Low; 3 = Neutral; 4 = High; 5 = Very High**

| Criteria                               | Task Difficulty       | Time Demand           |
| -------------------------------------- | --------------------- | --------------------- |
| Bob reusing existing data loading code | <input name="a4_1_d"> | <input name="a4_1_t"> |
| Bob manually writing data loading code | <input name="a4_2_d"> | <input name="a4_2_t"> |

<hr>

# Scenario B - Algorithm Design

> 💡 **Bob wants to evaluate a RT algorithm on multiple datasets**

**Bob** wants to pass **Alice’s** dataset through the RT algorithm, and check if the algorithm functions as it should. For this, **Bob** only needs 5 columns from each CSV file.

- `timestamp_ms` : timestamp in ms
- `gazepoint_x`: average x-position of both eyes
- `gazepoint_y`: average y-position of both eyes
- `pd_left` : pupil diameter of left eye
- `pd_right`: pupil diameter of right eye

**Bob** picked one CSV file and wrote a script (shown below) to run the algorithm.

```python
import pandas as pd
from impl import RTAlgorithm

if __name__ == "__main__":
  # read CSV file
  df_alg = pd.read_csv("/path/to/file.csv")
  # initialize the algorithm
  alg = RTAlgorithm()
	# run data SEQUENTIALLY through the algorithm
  for row in df_alg.rows()
    # get function args
    t = row.timestamp_ns
    x = row.gazepoint_x
    y = row.gazepoint_y
    d = (row.pd_left + row.pd_right) / 2 # take the average pd
    # call the algorithm
    out = alg.step(t,x,y,d)
    # print the output
    print(out)
    # if required, uncomment to rate-limit at 60 Hz
    # time.sleep(1/60)
```

<hr>

## Question B1

> 💡 Bob tries to understand the experimental variables (e.g., participants, tasks) in Alice’s dataset, and what its folder structure represents (e.g., one folder per task, one file per participant).
>
> This helps Bob to understand what types of statistical tests can be run on that dataset.

Based on your experience, please rate how **difficult** and **time-consuming** you think the process of **Bob finding the mapping between experimental variables and data units** could get, under each condition.

> **Quality of Documentation**
>
> - **Good -** Alice has created a detailed description of the dataset and its contents
> - **Poor -** Alice has not created any description for the dataset
>
> **Level of Communication**
>
> - **Good -** Alice is willing to answer any questions Bob might have
> - **Poor -** Alice doesn’t have time to answer any questions Bob might have
>
> **Format of Data Files**
>
> - **Open -** Alice saved data in a open filetype (CSV). Bob can view them without paid software.
> - **Closed -** Alice saved data in a closed filetype (EDF) from the recording software. Bob needs paid software to view them.

> **Scale : [1 = Very Low; 2 = Low; 3 = Neutral; 4 = High; 5 = Very High]**

| Docs | Comms | Filetype | Task Difficulty       | Time Demand           |
| ---- | ----- | -------- | --------------------- | --------------------- |
| Good | Good  | Open     | <input name="b1_1_d"> | <input name="b1_1_t"> |
| Good | Good  | Closed   | <input name="b1_2_d"> | <input name="b1_2_t"> |
| Good | Poor  | Open     | <input name="b1_3_d"> | <input name="b1_3_t"> |
| Good | Poor  | Closed   | <input name="b1_4_d"> | <input name="b1_4_t"> |
| Poor | Good  | Open     | <input name="b1_5_d"> | <input name="b1_5_t"> |
| Poor | Good  | Closed   | <input name="b1_6_d"> | <input name="b1_6_t"> |
| Poor | Poor  | Open     | <input name="b1_7_d"> | <input name="b1_7_t"> |
| Poor | Poor  | Closed   | <input name="b1_8_d"> | <input name="b1_8_t"> |

<hr>

## Question B2

> 💡 Bob tries to understand what each field (e.g., column, key/value) in the recordings of Alice’s dataset represents (e.g., each column is a measurement).
>
> This helps Bob to understand which fields to read from each recording, and what preprocessing steps to perform before running them through the RT algorithm.

Based on your experience, please rate how **difficult** and **time-consuming** you think the process of **Bob finding which fields to pass as arguments to `step(t,x,y,d)`** could get, under each condition.

> **Quality of Documentation**
>
> - **Good -** Alice has created a detailed description of the dataset and its contents
> - **Poor -** Alice has not created any description for the dataset
>
> **Level of Communication**
>
> - **Good -** Alice is willing to answer any questions Bob might have
> - **Poor -** Alice doesn’t have time to answer any questions Bob might have
>
> **Format of Data Files**
>
> - **Open -** Alice saved data in a open filetype (CSV). Bob can view them without paid software.
> - **Closed -** Alice saved data in a closed filetype (EDF) from the recording software. Bob needs paid software to view them.

> **Scale : [1 = Very Low; 2 = Low; 3 = Neutral; 4 = High; 5 = Very High]**

| Docs | Comms | Filetype | Task Difficulty       | Time Demand           |
| ---- | ----- | -------- | --------------------- | --------------------- |
| Good | Good  | Open     | <input name="b2_1_d"> | <input name="b2_1_t"> |
| Good | Good  | Closed   | <input name="b2_2_d"> | <input name="b2_2_t"> |
| Good | Poor  | Open     | <input name="b2_3_d"> | <input name="b2_3_t"> |
| Good | Poor  | Closed   | <input name="b2_4_d"> | <input name="b2_4_t"> |
| Poor | Good  | Open     | <input name="b2_5_d"> | <input name="b2_5_t"> |
| Poor | Good  | Closed   | <input name="b2_6_d"> | <input name="b2_6_t"> |
| Poor | Poor  | Open     | <input name="b2_7_d"> | <input name="b2_7_t"> |
| Poor | Poor  | Closed   | <input name="b2_8_d"> | <input name="b2_8_t"> |

<hr>

## Question B3

> 💡 Bob tries to mimic the real-world use case of his RT algorithm. In reality, a 60 Hz device would send data at 60 Hz, which means the RT algorithm will also be called at 60 Hz.
>
> To simulate such conditions from recorded data (i.e., Alice’s dataset), Bob must rate-limit the `step()` function to the sampling frequency of data. To perform this, Bob needs to know the sampling frequency, and implement the actual rate-limiting.

Based on your experience, please rate how **difficult** and **time-consuming** you think the process of **Bob finding the sampling frequency and implementing the rate-limiting** could get, under each condition.

> **Quality of Documentation**
>
> - **Good -** Alice has created a detailed description of the dataset and its contents
> - **Poor -** Alice has not created any description for the dataset
>
> **Level of Communication**
>
> - **Good -** Alice is willing to answer any questions Bob might have
> - **Poor -** Alice doesn’t have time to answer any questions Bob might have
>
> **Format of Data Files**
>
> - **Open -** Alice saved data in a open filetype (CSV). Bob can view them without paid software.
> - **Closed -** Alice saved data in a closed filetype (EDF) from the recording software. Bob needs paid software to view them.

> **Scale : [1 = Very Low; 2 = Low; 3 = Neutral; 4 = High; 5 = Very High]**

| Docs | Comms | Filetype | Task Difficulty       | Time Demand           |
| ---- | ----- | -------- | --------------------- | --------------------- |
| Good | Good  | Open     | <input name="b3_1_d"> | <input name="b3_1_t"> |
| Good | Good  | Closed   | <input name="b3_2_d"> | <input name="b3_2_t"> |
| Good | Poor  | Open     | <input name="b3_3_d"> | <input name="b3_3_t"> |
| Good | Poor  | Closed   | <input name="b3_4_d"> | <input name="b3_4_t"> |
| Poor | Good  | Open     | <input name="b3_5_d"> | <input name="b3_5_t"> |
| Poor | Good  | Closed   | <input name="b3_6_d"> | <input name="b3_6_t"> |
| Poor | Poor  | Open     | <input name="b3_7_d"> | <input name="b3_7_t"> |
| Poor | Poor  | Closed   | <input name="b3_8_d"> | <input name="b3_8_t"> |

<hr>

## Question B4

If you wish to find the peak data frequency that your algorithm can handle, would you rather have standard benchmark tests to compute them?

<input type="radio" name="b4" value="Y">
<label>Yes</label>
<br>
<input type="radio" name="b4" value="N">
<label>No</label>

<hr>

## Question B5

If you wish to quantify the performance (e.g., throughput, latency) of your algorithm, would you rather have standard benchmark tests to compute them?

<input type="radio" name="b5" value="Y">
<label>Yes</label>
<br>
<input type="radio" name="b5" value="N">
<label>No</label>

<hr>

# Scenario C - Improving Productivity

> 💡 **Cindy wants to streamline how datasets and algorithms are integrated at her lab.**

<hr>

## Question C1

Cindy’s students frequently run **multiple** datasets through **multiple** algorithms on a day-to-day basis. From your experience, rate how difficult and time-demanding this process could get.

> **Scale : [1 = Very Low; 2 = Low; 3 = Neutral; 4 = High; 5 = Very High]**

| Criteria                      | Rating              |
| ----------------------------- | ------------------- |
| Difficulty of the job tasks   | <input name="c1_1"> |
| Time needed for the job tasks | <input name="c1_2"> |

<hr>

## Question C2

Would you agree that such integration must be automated whenever possible?

<input type="radio" name="c2" value="Y">
<label>Yes</label>
<br>
<input type="radio" name="c2" value="N">
<label>No</label>

<hr>

## Question C3

Given the opportunity to change how Cindy’s lab operates, rate how the changes suggested below could impact lab productivity.

**Scale: [1 = Very Negative; 2 = Negative; 3 = None; 4 = Positive; 5 = Very Positive]**

| Details of Change                                                           | Rating              |
| --------------------------------------------------------------------------- | ------------------- |
| Having a system to annotate datasets once, and reuse them on new algorithms | <input name="c3_1"> |
| Having a Python API to read data from any annotated dataset                 | <input name="c3_2"> |

<hr>

<button type="submit">Submit</button>

</form>
