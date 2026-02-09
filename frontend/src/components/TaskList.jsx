import React, { useState, useMemo } from 'react';
import { useNotification } from './Notification';
import { useTasks } from '../contexts/TasksContext';

const TaskList = ({ onTaskUpdate, onTaskDelete }) => {
  const { tasks, loading, error, toggleTaskCompletion, deleteTask } = useTasks();
  const { addNotification } = useNotification();
  
  // State for filters and sorting
  const [filter, setFilter] = useState('all'); // all, active, completed
  const [sortBy, setSortBy] = useState('created_at'); // created_at, updated_at, due_date, priority
  const [sortOrder, setSortOrder] = useState('desc'); // asc, desc
  const [searchTerm, setSearchTerm] = useState('');

  const handleToggleCompletion = async (task) => {
    try {
      await toggleTaskCompletion(task);
      if (onTaskUpdate) onTaskUpdate(task);
    } catch (err) {
      // Error handling is done in the context
    }
  };

  const handleDeleteTask = async (task) => {
    try {
      await deleteTask(task.id);
      if (onTaskDelete) onTaskDelete(task.id);
    } catch (err) {
      // Error handling is done in the context
    }
  };

  // Filter and sort tasks
  const filteredAndSortedTasks = useMemo(() => {
    let filtered = tasks;

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(task => 
        task.title.toLowerCase().includes(term) ||
        (task.description && task.description.toLowerCase().includes(term)) ||
        (task.tags && task.tags.toLowerCase().includes(term))
      );
    }

    // Apply status filter
    if (filter === 'active') {
      filtered = filtered.filter(task => !task.is_completed);
    } else if (filter === 'completed') {
      filtered = filtered.filter(task => task.is_completed);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue, bValue;

      switch (sortBy) {
        case 'due_date':
          aValue = a.due_date ? new Date(a.due_date) : new Date(8640000000000000); // Max date for null values
          bValue = b.due_date ? new Date(b.due_date) : new Date(8640000000000000);
          break;
        case 'priority':
          const priorityOrder = { high: 3, medium: 2, low: 1 };
          aValue = priorityOrder[a.priority] || 0;
          bValue = priorityOrder[b.priority] || 0;
          break;
        case 'updated_at':
          aValue = new Date(a.updated_at);
          bValue = new Date(b.updated_at);
          break;
        case 'created_at':
        default:
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
          break;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [tasks, filter, sortBy, sortOrder, searchTerm]);

  if (loading) return <div className="loading">Loading tasks...</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <div className="task-list">
      <div className="task-list-controls">
        <h2>Your Tasks</h2>
        
        {/* Search bar */}
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search tasks..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        
        {/* Filters and sorting controls */}
        <div className="filters-sorting">
          <div className="filter-group">
            <label htmlFor="filter">Status:</label>
            <select
              id="filter"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label htmlFor="sortBy">Sort by:</label>
            <select
              id="sortBy"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="filter-select"
            >
              <option value="created_at">Created Date</option>
              <option value="updated_at">Updated Date</option>
              <option value="due_date">Due Date</option>
              <option value="priority">Priority</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label htmlFor="sortOrder">Order:</label>
            <select
              id="sortOrder"
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="filter-select"
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>
      </div>

      {filteredAndSortedTasks.length === 0 ? (
        <div className="empty-state">
          <h3>No tasks found</h3>
          <p>{searchTerm ? 'Try a different search term.' : 'Create your first task to get started!'}</p>
        </div>
      ) : (
        <ul className="task-list-ul">
          {filteredAndSortedTasks.map(task => (
            <li key={task.id} className={`task-item ${task.is_completed ? 'completed' : ''}`}>
              <div className="task-content">
                <input
                  type="checkbox"
                  checked={task.is_completed}
                  onChange={() => handleToggleCompletion(task)}
                  className="task-checkbox"
                  aria-label={task.is_completed ? `Mark ${task.title} as incomplete` : `Mark ${task.title} as complete`}
                />
                <div className="task-text">
                  <h3>{task.title}</h3>
                  {task.description && <p>{task.description}</p>}
                  
                  {/* Display advanced fields */}
                  <div className="task-details">
                    {task.due_date && (
                      <span className={`task-due-date ${new Date(task.due_date) < new Date() && !task.is_completed ? 'overdue' : ''}`}>
                        Due: {new Date(task.due_date).toLocaleDateString()} {new Date(task.due_date) < new Date() && !task.is_completed ? '(Overdue)' : ''}
                      </span>
                    )}
                    
                    <span className={`task-priority priority-${task.priority}`}>
                      Priority: {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
                    </span>
                    
                    {task.tags && (
                      <div className="task-tags">
                        Tags: {task.tags.split(',').map(tag => tag.trim()).join(', ')}
                      </div>
                    )}
                  </div>
                  
                  <div className="task-meta">
                    <span>Created: {new Date(task.created_at).toLocaleDateString()}</span>
                    <span>Updated: {new Date(task.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
              <div className="task-actions">
                <button
                  onClick={() => onTaskUpdate && onTaskUpdate(task)}
                  className="btn btn-secondary"
                  aria-label={`Edit task: ${task.title}`}
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDeleteTask(task)}
                  className="btn btn-error"
                  aria-label={`Delete task: ${task.title}`}
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TaskList;