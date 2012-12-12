'''
Created on Dec 12, 2012

@author: nathan
'''

from bottle import run
import app


def main():
    run(app.app)

if __name__ == '__main__':
    main()