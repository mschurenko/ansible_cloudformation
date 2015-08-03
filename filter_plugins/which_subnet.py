from ansible import errors

def subnet(num,subnets):
  if not isinstance(subnets, list):
    raise errors.AnsibleError('subnets must be a list.')
    
  start = 1
  end = 10000
  sl = len(subnets)
  d = {}

  inst_range = range(start, end + 1)
  while True:
    x = 0
    for inst in inst_range[0:sl]:
      d[inst] = subnets[x]
      x += 1

    for i in inst_range[0:sl]: inst_range.remove(i)
    if len(inst_range) == 0: break

  if int(num) in d:
    return d[int(num)]
  else:
    raise errors.AnsibleError('%s is not a number' % str(num))

class FilterModule(object):
  def filters(self):
    return {
      'which_subnet' : subnet
    }
