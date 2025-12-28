from express_entry import render as express_entry_render
from ucalgary_mba.py import render as ucalgary_mba_render

def render():
    express_entry_render()
    ucalgary_mba_render()

if __name__ == "__main__":
    render()