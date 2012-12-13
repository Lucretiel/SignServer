'''
Created on Dec 12, 2012

@author: nathan
'''

from bottle import run
import app


def main():
    run(app.app, host='0.0.0.0', port=39999)

if __name__ == '__main__':
    main()