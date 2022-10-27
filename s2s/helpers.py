import random
import string


def print_changelog():
    """
    Returns
    -------
    changelog : list of logs
    """

    changelog = [
        {"minor version": 0, "details": "initial POC commit", "date": "2022-09-14"},
        {"minor version": 1, "details": "adds version changelog", "date": "2022-09-14"},
        {"minor version": 2, "details": "adds multichannel", "date": "2022-09-14"},
        {
            "minor version": 3,
            "details": "improves UI for Sender/Receiver",
            "date": "2022-09-15",
        },
        {
            "minor version": 4,
            "details": "adds automatic scrolling in Sender table",
            "date": "2022-09-15",
        },
        {
            "minor version": 5,
            "details": "adds timestamp of segment processing",
            "date": "2022-09-15",
        },
        {"minor version": 6, "details": "adds logfile", "date": "2022-09-15"},
        {
            "minor version": 7,
            "details": "adds parameter to reduce calls of API",
            "date": "2022-09-16",
        },
        {
            "minor version": 8,
            "details": "adds feature to improve accuracy with list of terms",
            "date": "2022-09-17",
        },
        {
            "minor version": 9,
            "details": "improves SENDER UI; fix sampling frequency logic",
            "date": "2022-09-19",
        },
        {"minor version": 10, "details": "improves Receiver UI;", "date": "2022-09-19"},
        {
            "minor version": 11,
            "details": "improves sampling frequency logic from APP",
            "date": "2022-09-20",
        },
        {
            "minor version": 12,
            "details": "improves UI Sender; make logging optional (hard coded switch)",
            "date": "2022-09-21",
        },
        {
            "minor version": 13,
            "details": "adds optional AI rephrasing for longer sentences >20 tokens",
            "date": "2022-09-21",
        },
        {
            "minor version": 14,
            "details": "adds API initialisation call with sessionID",
            "date": "2022-09-21",
        },
        {
            "minor version": 15,
            "details": "minor improvements to Receiver UI",
            "date": "2022-09-22",
        },
        {
            "minor version": 16,
            "details": "adds multilingual support",
            "date": "2022-09-22",
        },
        {
            "minor version": 17,
            "details": "adding new timer logic",
            "date": "2022-09-29",
        },
        {
            "minor version": 18,
            "details": "adding controller of voice speed in SENDER",
            "date": "2022-10-02",
        },
        {
            "minor version": 19,
            "details": "new control of session initialisation for segmentation API",
            "date": "2022-10-05",
        },
        {
            "minor version": 20,
            "details": "improved responsivness of RECEIVER",
            "date": "2022-10-06",
        },
        {
            "minor version": 21,
            "details": "adding simple SENDER page with standard settings",
            "date": "2022-10-12",
        },
        {
            "minor version": 22,
            "details": "adding simple login page",
            "date": "2022-10-13",
        },
        {"minor version": 23, "details": "cleaning code", "date": "2022-10-17"},
        {
            "minor version": 24,
            "details": "fix stop translation after 10 segments",
            "date": "2022-10-18",
        },
    ]

    return changelog
