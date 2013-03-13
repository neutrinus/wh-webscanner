import os
from glob import glob

from .. import file_type_guesser


def build_classifier(training_files):
    cls = file_type_guesser.TextFileTypeGuesser()
    cls.train(training_files)
    cls._cls.show_most_informative_features()
    return cls


def pytest_generate_tests(metafunc):
    p = os.path.join(os.path.dirname(__file__), 'samples', '*', '*')
    files = {file_path: os.path.basename(os.path.dirname(file_path)) for file_path in glob(p)}
    number_of_sets = 3  # crossvalidation step, divede while file set for $number_of_sets$, one set is used for training

    sets = [{} for _ in xrange(number_of_sets)]

    # split all files across defined sets
    for num, (file_path, file_type) in enumerate(files.iteritems()):  # test one leave out
        sets[num % number_of_sets][file_path] = file_type

    function_values = []
    for testing_set_number in xrange(number_of_sets):
        training_sets = {}
        for num, training_set in enumerate(sets):
            if num == testing_set_number:
                continue
            training_sets.update(training_set)

        function_values.append(({file_path: file_type for file_path, file_type in sets[testing_set_number].iteritems()}, training_sets))

    metafunc.parametrize(('files_to_check', 'training_files'),
                         function_values)


def test_naive_bayes(files_to_check, training_files):
        cls = build_classifier(training_files)

        for file_to_check in files_to_check.iterkeys():
            assert file_to_check not in training_files  # only to be sure :)

        successes, fails = 0, 0
        for file_to_check in files_to_check.iteritems():
            gues_t = cls.guess_from_file(file_to_check[0])

            if gues_t == file_to_check[1]:
                successes += 1
            else:
                fails += 1

        ratio = successes / float(successes + fails) * 100.0
        print 'Results: successes: %d, fails: %d, ratio: %.2f%%' % (successes, fails, ratio)
        assert ratio > 98.0
