import requests
import time
import json
import sys

# default production batch instances scheduler interval is 20 seconds
TIMEOUT = 900
API_URL = "https://internetnl-assessment.online/api/batch/v2/"


def wait_for_request_status(url, expected_status, timeout=10, interval=1, auth=None):
    """Poll url and parse JSON for request.status, return if value matches expected status or
    fail when timeout expires."""
    max_tries = int(timeout / interval)

    tries = 0
    while tries < max_tries:
        status_response = requests.get(url, auth=auth, verify=False)
        status_response.raise_for_status()

        print(status_response.text)
        status_data = status_response.json()
        if status_data["request"]["status"] == expected_status:
            break
        time.sleep(interval)
        tries += 1
    else:
        assert False, f"request status never reached '{expected_status}' state"

    return status_data


def make_batch_request(domains, unique_id, api_auth, request_type):
    request_data = {"type": request_type, "domains": domains, "name": unique_id}
    auth = api_auth

    # start batch request
    register_response = requests.post(
        api_url + "requests", json=request_data, auth=auth, verify=False
    )
    register_response.raise_for_status()
    print(register_response.text)

    # batch request start response
    register_data = register_response.json()
    test_id = register_data["request"]["request_id"]

    # wait for batch tests to start
    wait_for_request_status(
        api_url + "requests/" + test_id, "running", timeout=TIMEOUT, auth=auth
    )

    # wait for batch tests to complete and report to be generated
    wait_for_request_status(
        api_url + "requests/" + test_id,
        "generating",
        interval=2,
        timeout=2 * TIMEOUT,
        auth=auth,
    )

    # wait for report generation and batch to be done
    wait_for_request_status(
        api_url + "requests/" + test_id, "done", timeout=TIMEOUT, auth=auth
    )

    # get batch results
    results_response = requests.get(
        api_url + "requests/" + test_id + "/results", auth=auth, verify=False
    )
    results_response.raise_for_status()

    # batch results contents
    results_response_data = results_response.json()
    with open(f"{request_type}.json", "w") as f:
        json.dump(results_response_data, f)

    # get batch technical results
    results_technical_response = requests.get(
        api_url + "requests/" + test_id + "/results_technical", auth=auth, verify=False
    )
    results_technical_response.raise_for_status()

    # batch technical results
    results_technical_response_data = results_technical_response.json()
    with open(f"{request_type}_technical.json", "w") as f:
        json.dump(results_technical_response_data, f)


with open(sys.argv[1], "r") as f:
    domains = [line.rstrip() for line in f.readlines()]

make_batch_request(
    domains,
    sys.argv[1],
    (input("Batch username: "), input("Batch password: ")),
    input("Type [mail/web]: "),
)
