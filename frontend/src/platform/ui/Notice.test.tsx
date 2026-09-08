import {it,expect} from 'vitest'
import {render,screen} from '@testing-library/react'
import {ErrorNotice,EmptyState} from './Notice'
import {ApiError} from '../api/client'
it('error is an alert containing a support correlation ID',()=>{render(<ErrorNotice error={new ApiError(409,'conflict','Changed elsewhere','req123')}/>);expect(screen.getByRole('alert')).toHaveTextContent('req123')})
it('empty state is distinct from a failed request',()=>{render(<EmptyState title="No records" description="Create a record."/>);expect(screen.queryByRole('alert')).not.toBeInTheDocument();expect(screen.getByRole('heading',{name:'No records'})).toBeVisible()})
