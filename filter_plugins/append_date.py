import datetime

def date(string):
  ''' take a string and append the date to it'''
  return string + '-' + str(datetime.date.today())

class FilterModule(object):
  def filters(self):
    return {
      'append_date' : date
    }
