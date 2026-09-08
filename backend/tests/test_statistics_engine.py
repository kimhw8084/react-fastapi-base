from math import isclose
import pytest

from app.platform.statistics import c_chart, capability, correlation, cusum, descriptive, ewma, imr, linear_regression, np_chart, p_chart, pareto, run_rule_flags, u_chart, xbar_r, xbar_s


def test_descriptive_and_imr_are_deterministic():
    values=[10,11,10,12,11,10,9,10]
    summary=descriptive(values)
    assert summary['count']==8 and summary['minimum']==9 and summary['maximum']==12
    chart=imr(values)
    assert isclose(chart['center'],10.375)
    assert chart['moving_ranges']==[1,1,2,1,1,1,1]
    assert chart['lower_control'] < min(values) < max(values) < chart['upper_control']


def test_xbar_r_equal_groups_and_guards():
    result=xbar_r([[10,11,9,10],[10,10,11,9],[12,11,10,11],[9,10,9,10]])
    assert result['subgroup_size']==4
    assert len(result['means'])==4 and len(result['ranges'])==4
    assert result['xbar_lower'] < result['xbar_center'] < result['xbar_upper']
    with pytest.raises(ValueError):xbar_r([[1,2],[1,2,3]])
    with pytest.raises(ValueError):xbar_r([[1],[2]])


def test_capability_uses_within_and_overall_sigma():
    values=[99.7,100.2,100.1,99.9,100.0,100.3,99.8,100.1,100.0,99.9]
    result=capability(values,lower_spec=99,upper_spec=101)
    assert result['cp'] is not None and result['cp'] > 1
    assert result['cpk'] is not None and result['cpk'] > 1
    assert result['pp'] is not None and result['ppk'] is not None
    with pytest.raises(ValueError):capability(values)
    with pytest.raises(ValueError):capability(values,lower_spec=1,upper_spec=1)


def test_ewma_pareto_and_run_rules():
    assert ewma([10,12,14],alpha=.5)==[10,11,12.5]
    with pytest.raises(ValueError):ewma([1,2],alpha=0)
    ranked=pareto(['A','B','A','C','A','B'])
    assert [row['category'] for row in ranked]==['A','B','C']
    assert ranked[-1]['cumulative_percent']==100
    flags=run_rule_flags([1,2,3,4,5,6,7,8,9,10],center=0)
    assert 7 in flags['eight_on_one_side']
    assert 5 in flags['six_point_trend']


def test_xbar_s_attribute_charts_and_cusum_are_deterministic():
    result=xbar_s([[10,11,9,10],[10,10,11,9],[12,11,10,11],[9,10,9,10]])
    assert result['subgroup_size']==4 and len(result['standard_deviations'])==4
    p=p_chart([1,2,1,3],[10,10,10,10]);assert p['center']==.175 and len(p['proportions'])==4
    assert np_chart([1,2,1],10)['center']==pytest.approx(4/3)
    assert c_chart([1,2,1])['center']==pytest.approx(4/3)
    assert len(u_chart([1,2,1],[10,20,10])['rates'])==3
    assert cusum([10,10,12],target=10)['positive'][-1]==pytest.approx(2)


def test_correlation_and_regression_have_known_values_and_zero_variance_guards():
    assert correlation([1,2,3],[2,4,6])==pytest.approx(1)
    fit=linear_regression([1,2,3],[2,4,6]);assert fit['slope']==pytest.approx(2) and fit['intercept']==pytest.approx(0) and fit['r_squared']==pytest.approx(1)
    with pytest.raises(ValueError):correlation([1,1,1],[2,3,4])
    with pytest.raises(ValueError):linear_regression([1,1,1],[2,3,4])
