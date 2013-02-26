#!/usr/bin/python

'''
            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Copyright (C) 2013 Saurabh Dingolia <dinsaurabh123@gmail.com>

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.

'''

import sys
import os
import re
import math  
import itertools
from collections import Counter


def main():
  args = sys.argv[1:]   # Get the arguments
  
  if not args or not len(args) == 4:
    _exit()
    
  if ( not args[0] == '--data' or not os.path.isfile(args[1]) or 
       not args[2] == '--sup' or not os.path.isfile(args[3]) ):
    _exit()
    
  # Define global variables
  global output_patterns, sdc, output_dir
  output_patterns = []    # To hold the output frequent sequential patterns
  
  output_dir = os.path.abspath(os.path.join(args[1], os.pardir))
  print output_dir
  
  # Read the data file
  in_file = open(args[1], 'rU')
  text = in_file.read();
  in_file.close()
  
  # Parse the data in_file to create nested list of data sequences
  text = text.replace('<{', '').replace('}>', '')
  sequences = text.split("\n")
  sequences = [ sequence.split("}{") for sequence in sequences if sequence]
  sequences = [[[item.strip() for item in itemset.split(",")] for itemset in sequence] for sequence in sequences]

  # Read the support file
  in_file = open(args[3], 'rU')
  text = in_file.read()
  in_file.close()
  
  # Parse the support in_file to create support dict and retrieve support difference constraint
  mis_values = { match[0]: float(match[1]) for match in re.findall(r'MIS\((\w+)\)\s+=\s+(\d*\.?\d*)', text) }
  sdc = float(re.search(r'SDC\s=\s(\d*\.?\d*)', text).group(1))
  
  # Run the Multiple Support Prefix Span algorithm
  begin_msps(sequences, mis_values, sdc)


def _exit(message=None):
  if message == None:
    message = 'usage: --data datafile --sup supportfile'
  print message
  sys.exit(1)
  

def begin_msps(sequences, mis_values, sdc):
  if (  sequences == None or len(sequences) == 0 or
        mis_values == None or len(mis_values) == 0  ):
    print 'Invalid data sequence or minimum support values'
    return;
  
  # Total no. of data sequences
  sequence_count = len(sequences)
  
  # Get the item support for each item i.e. sup(i)
  global actual_supports
  flattened_sequences = [ list(set(itertools.chain(*sequence))) for sequence in sequences ]
  support_counts = dict(Counter(item for flattened_sequence in flattened_sequences for item in flattened_sequence)) 
  actual_supports = {item:support_counts.get(item)/float(sequence_count) for item in support_counts.keys()}
  del flattened_sequences
  
  # Get the sorted list of frequent items i.e items with sup(i) >= MIS(i)
  frequent_items = sorted([item for item in actual_supports.keys() if actual_supports.get(item) >= mis_values.get(item)],key=mis_values.get)
#  print "FrequentItems:",frequent_items
  
  # Iterate through frequent items to get sequential patterns
  for item in frequent_items:
    # Get the minimum item support count for item i.e count(MIS(item))
    mis_count = int(math.ceil(mis_values.get(item)*len(sequences)))
    
    print "------------- Current item:",item,"MIS:",mis_count, "Sup:",support_counts.get(item),"-----------------"
#    print "Seq:", [sequence for sequence in sequences if has_item(sequence, item)]
       
    # Get the sequences containing that item and filter them to remove elements that do not satisfy SDC i.e. |sup(j) - sup(item)| > sdc
    item_sequences = [sdc_filter_on_item(sequence, item, actual_supports.get(item), actual_supports, sdc) for sequence in sequences if has_item(sequence, item)]
#    print "ItemSeq:"
#    print "\n".join([str(sequence) for sequence in item_sequences])
    
    # Run the restricted Prefix-Span to get sequential patterns
    r_prefix_span(item, item_sequences, mis_count)
    
    # Remove the item from original sequences
    sequences = remove_item(sequences, item)
    
  # End of the mining algorithm, print output
  write_output(output_patterns)


def write_output(output_list):
  output_list = sorted(output_list,key=pattern_length)    # Sort the output based on pattern length
  output_text = ''    # Intialize empty string to append the output text
  
  cur_length = 1    # Initialize current length as 1 
  
  while True:   # Iterate until there are no patterns of specified length
    # Get all the patterns of current length from output 
    cur_length_patterns = filter (lambda a: pattern_length(a) == cur_length, output_list)
    if not cur_length_patterns:   # Break from the loop if the list is empty 
      break
    
    # Print the current length and number of patterns for current length
    output_text += "The number of length " + str(cur_length) + " sequential patterns is " + str(len(cur_length_patterns)) + "\n"
    
    # Print all the patterns with their support counts
    for (pattern,sup_count) in cur_length_patterns:
      str_pattern = "<{" + "}{".join([",".join(itemset) for itemset in pattern]) + "}>"
      output_text += "Pattern: " + str_pattern + " Count: " + str(sup_count) + "\n"
    
    cur_length += 1   # Increment the current length 
    
    output_text += "\n"
  
  print output_text
  output_file = open(output_dir + "/" + "results.txt", 'w')
  output_file.write(output_text)
  output_file.close()
    
      
def pattern_length(output_tuple):
  seq_pattern = output_tuple[0]   # Get the sequential pattern
  
  while isinstance(seq_pattern[0], list):   # Chain it until all sub-lists are removed
    seq_pattern = list(itertools.chain(*seq_pattern))
  
  return len(seq_pattern)   # Return the length of the pattern


def remove_item(source_list, item_to_del):
  filtered_list = []    # Declare list to contain filter results
  
  # Check to see if list has sub lists as items   
  if source_list and isinstance(source_list[0], list):
    
    for child_list in source_list:
      filtered_child_list = remove_item(child_list, item_to_del)    # Recurse for filtering each child_list
      
      if filtered_child_list:   # Append only non-empty lists
        filtered_list.append(filtered_child_list)  
    
  else:   # Remove item from the list
    filtered_list = filter (lambda a: a != item_to_del, source_list)

  return filtered_list    # Return the filtered list from current recursion
  
  
def sdc_filter_on_item(source_list, base_item, base_item_support, supports, sd_constraint):
  filtered_list = []    # Declare list to contain filter results
  
  # Check to see if list has sub lists as items    
  if source_list and isinstance(source_list[0], list):
    for child_list in source_list:
      filtered_child_list = sdc_filter_on_item(child_list, base_item, base_item_support, supports, sd_constraint)    # Recurse for filtering each child_list
      if filtered_child_list:   # Append only the non-empty lists
        filtered_list.append(filtered_child_list)  
    
  else:   # Remove items that do not satisfy support difference constraint
    for item in source_list:
#      print "Item:",item,"Support:",item_supports.get(item),"Diff:",abs(item_supports.get(item) - base_item_support)
      if not item == base_item and abs(supports.get(item) - base_item_support) > sd_constraint:  # Item doesn't satisfy SDC
        continue
      else:   # Item satisfies SDC
        filtered_list.append(item)

  return filtered_list    # Return the filtered list from current recursion


def r_prefix_span(base_item, item_sequences, mis_count):
  # Get the frequent items and construct length one frequent sequences from them
  freq_item_sequences = remove_infrequent_items(item_sequences, mis_count)
  frequent_items = list(set(itertools.chain(*(itertools.chain(*freq_item_sequences)))))
  del freq_item_sequences
  
  # Get length-1 frequent sequences
  len_1_freq_sequences = [ [[item]] for item in frequent_items ]
#  print len_1_freq_sequences
  
  # Add the base_item 1-length sequential pattern to the output database
  if has_item(len_1_freq_sequences, base_item):
    output_patterns.append(([[base_item]], support_count(item_sequences, base_item)))
  
  # Run Prefix Span for each length-1 frequent sequential pattern    
  for freq_sequence in len_1_freq_sequences:
    prefix_span(freq_sequence, item_sequences, base_item, mis_count)
  

def prefix_span(prefix, item_sequences, base_item, mis_count):
  print "Prefix:",prefix
  
  # Compute the projected database for the current prefix
  projected_db = compute_projected_database(prefix, item_sequences, base_item, mis_count)
#  print "DB:"
#  print "\n".join([str(sequence) for sequence in projected_db])
  
  # Find the prefix_length + 1 sequential patterns 
  if projected_db:    # Check if the projected database has any sequences
    
    # Initialize local variables
    prefix_last_itemset = prefix[-1]    # Last itemset in prefix
    all_template_1_items = []   # To hold all items for template 1 match i.e {30, x} or {_, x}
    all_template_2_items = []   # To hold all items for template 2 match i.e {30}{x}
    
    for proj_sequence in projected_db:
      itemset_index = 0
      template_1_items = []   # To hold items for template 1 match from current sequence
      template_2_items = []   # To hold items for template 2 match from current sequence
      
      while itemset_index < len(proj_sequence):   # Iterate through itemsets in sequence
        cur_itemset = proj_sequence[itemset_index]    # Current itemset in sequence
        
        if has_item(cur_itemset, '_'):    # Add the items following '_' to template 1 list if it's a {_, x} match
          template_1_items += cur_itemset[1:]
        
        # Itemset doesn't contain '_', check for other matches
        else:
          if contains_in_order(cur_itemset, prefix_last_itemset):    # Check if current itemset contains last itemset of prefix i.e {30, x} match
            template_1_items += cur_itemset[cur_itemset.index(prefix_last_itemset[-1])+1:]    # Add the items following prefix's last itemset's last item from the current itemset 
          
          template_2_items += cur_itemset  # Add all the items in current itemset to template 2 list i.e {30}{x} match
        
        itemset_index += 1
      
      # Add only the unique elements from both lists of current sequence to the main lists as each element is considered only once for a sequence
      all_template_1_items += list(set(template_1_items))   
      all_template_2_items += list(set(template_2_items))
  
#    print "Template 1 items:", all_template_1_items
#    print "Template 2 items:", all_template_2_items
    
    # Compute the total occurences of each element for each template i.e number of sequences it satisfied for a template match
    dict_template_1 = dict(Counter(item for item in all_template_1_items))
    dict_template_2 = dict(Counter(item for item in all_template_2_items))
    
#    print "Template 1 item support:", dict_template_1
#    print "Template 2 item support:", dict_template_2 
    
    freq_sequential_patterns = []  # Initialize empty list to contain obtained sequential patterns
    
    # For both the template matches, generate freuqent sequential patterns i.e patterns having support count >= MIS count
    for item, sup_count in dict_template_1.iteritems():
      if sup_count >= mis_count:
        # Add the item to the last itemset of prefix for obtaining the pattern
        freq_sequential_patterns.append((prefix[:-1] + [prefix[-1] + [item]], sup_count))    # Add the pattern with its support count to frequent patterns list
    
    for item, sup_count in dict_template_2.iteritems():
      if sup_count >= mis_count:
        # Append the item contained in a new itemset to the prefix
        freq_sequential_patterns.append((prefix + [[item]], sup_count))    # Add the pattern with its support count to frequent patterns list
    
    print "Sequential Patterns Before SDC:", [pattern for pattern, sup_count in freq_sequential_patterns]  
    freq_sequential_patterns = [(pattern, sup_count) for pattern, sup_count in freq_sequential_patterns if is_sequence_sdc_satisfied(list(set(itertools.chain(*pattern))))]
    print "Sequential Patterns After SDC:", [pattern for pattern, sup_count in freq_sequential_patterns]  
        
    for (seq_pattern, sup_count) in freq_sequential_patterns:   # Iterate through patterns obtained
      if has_item(seq_pattern, base_item):    # Add the pattern to the output list if it contains base item
        output_patterns.append((seq_pattern, sup_count))    
      prefix_span(seq_pattern, item_sequences, base_item, mis_count)  # Call prefix_span recursively with the pattern as prefix
      
    
def compute_projected_database(prefix, item_sequences, base_item, mis_count):
  projected_db = []
  
  # Populate the projected database with projected sequences
  for sequence in item_sequences:
    
    cur_pr_itemset = 0
    cur_sq_itemset = 0
    
    while cur_pr_itemset < len(prefix) and cur_sq_itemset < len(sequence):
      if contains_in_order(sequence[cur_sq_itemset], prefix[cur_pr_itemset]):    # Sequence itemset contains the prefix itemset, move to next prefix itemset
        cur_pr_itemset += 1
        if cur_pr_itemset == len(prefix): break   # All prefix itemsets are present in the sequence
      
      cur_sq_itemset += 1   # Move to next sequence itemset
    
    if cur_pr_itemset == len(prefix):   # Prefix was present in the current sequence
      projected_sequence = project_sequence(prefix[-1][-1], sequence[cur_sq_itemset:])  # Get the projected sequence
      
      if projected_sequence:    # Non-empty sequence, add to projected database
        projected_db.append(projected_sequence)
  
#  print "DB1:"
#  print "\n".join([str(sequence) for sequence in projected_db])
  
  # Remove the infrequent items
  projected_db = remove_infrequent_items(projected_db, mis_count)
  
#  print "DB2:"
#  print "\n".join([str(sequence) for sequence in projected_db])
  
  # Check if any frequent items are left
  validation_db = remove_empty_elements([[[item for item in itemset if not item == '_'] for itemset in sequence] for sequence in projected_db])
  
  if validation_db:   # Non-empty database
#    projected_db = sdc_filter(projected_db)  # Remove sequences that do not satisfy SDC
    return remove_empty_elements(projected_db)    # Remove empty elements and return the projected database
  
  else:   # Empty database
    return validation_db
    
    
def project_sequence(prefix_last_item, suffix):
  suffix_first_itemset = suffix[0]
      
  if prefix_last_item == suffix_first_itemset[-1]:    # Template 2 projection, return suffix - current_itemset 
    return suffix[1:]
  else:   # Template 1 projection, remove items from first itemset of suffix that are before the index of prefix's last item and put '_' as first element
    suffix[0] = ['_'] + suffix_first_itemset[suffix_first_itemset.index(prefix_last_item)+1:]
    return suffix


def support_count(sequences, req_item):
  flattened_sequences = [ list(set(itertools.chain(*sequence))) for sequence in sequences ]
  support_counts = dict(Counter(item for flattened_sequence in flattened_sequences for item in flattened_sequence))
  
  return support_counts.get(req_item)

  
def contains(big, small):
  return len(set(big).intersection(set(small))) == len(small)


def contains_in_order(sq_itemset, pr_itemset):
  if(contains(sq_itemset, pr_itemset)):
    cur_pr_item = 0
    cur_sq_item = 0
    
    while cur_pr_item < len(pr_itemset) and cur_sq_item < len(sq_itemset):
      if pr_itemset[cur_pr_item] == sq_itemset[cur_sq_item]:
        cur_pr_item += 1
        if cur_pr_item == len(pr_itemset): return True
      
      cur_sq_item += 1
   
  return False 
        

def has_item(source_list, item):
  if source_list:
    while isinstance(source_list[0], list):
      source_list = list(itertools.chain(*source_list))
    
    return item in source_list  
  return False


def sdc_filter(projected_database):
#  filtered_database = [[itemset for itemset in sequence if is_sdc_satisfied(itemset)] for sequence in projected_database]
#  filtered_database = [sequence for sequence in projected_database if is_sequence_sdc_satisfied(sequence)]
  flattened_sequences = [ list(set(itertools.chain(*sequence))) for sequence in projected_database ]
  filtered_database = [sequence for i,sequence in enumerate(projected_database) if is_sequence_sdc_satisfied(flattened_sequences[i])]   
  return filtered_database


def is_sdc_satisfied(itemset):
  if not itemset:
    return False
  
  for item1 in itemset:
    sup_item1 = actual_supports.get(item1)
    for item2 in itemset:
      if not item1 == '_' and not item2 == '_':
        if abs(sup_item1 - actual_supports.get(item2)) > sdc:
          return False
      
  return True


def is_sequence_sdc_satisfied(sequence):
  if not sequence:
    return False
  
  print sequence 
  if len(sequence) > 1:
    for item1 in sequence:
      sup_item1 = actual_supports.get(item1)
      for item2 in sequence:
        if not item1 == '_' and not item2 == '_' and not item1 == item2:
          if abs(sup_item1 - actual_supports.get(item2)) > sdc:
            print "False"
            return False 
  print "True"        
  return True  


#def is_sequence_sdc_satisfied(sequence):
#  if not sequence:
#    return False
#  
#  for itemset in sequence:
#    for item1 in itemset:
#      sup_item1 = actual_supports.get(item1)
#      for item2 in itemset:
#        if not item1 == '_' and not item2 == '_':
#          if abs(sup_item1 - actual_supports.get(item2)) > sdc:
#            return False
#      
#  return True    
        

def remove_infrequent_items(item_sequences, min_support_count):
  # Get the support count for each item in supplied sequence database
  flattened_sequences = [ list(set(itertools.chain(*sequence))) for sequence in item_sequences ]
  support_counts = dict(Counter(item for flattened_sequence in flattened_sequences for item in flattened_sequence))
  
  # Remove the infrequent items from the sequence database  
  filtered_item_sequences = [[[item for item in itemset if support_counts.get(item) >= min_support_count or item == '_']for itemset in sequence] for sequence in item_sequences]
  
  return remove_empty_elements(filtered_item_sequences)    # Return the new sequence database
    

def remove_empty_elements(source_list):
  filtered_list = []    # Declare list to contain filter results
  
  # Check to see if list has sub lists as items   
  if source_list and isinstance(source_list[0], list):
        
    for child_list in source_list:
      filtered_child_list = remove_empty_elements(child_list)    # Recurse for filtering each child_list
      
      if filtered_child_list:   # Append only non-empty lists
        filtered_list.append(filtered_child_list)
  
  else:
    filtered_list = source_list 
   
  return filtered_list    # Return the filtered list from current recursion

  
if __name__ == '__main__':
  main()  
