import React, { useState, useEffect } from 'react';
import { useNotification } from './Notification';

const TaskForm = ({ onTaskCreated, taskToEdit, onEditComplete }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [priority, setPriority] = useState('medium');
  const [tags, setTags] = useState('');
  const [loading, setLoading] = useState(false);
  const { addNotification } = useNotification();

  // Populate form when taskToEdit changes
  useEffect(() => {
    if (taskToEdit) {
      setTitle(taskToEdit.title);
      setDescription(taskToEdit.description || '');
      setDueDate(taskToEdit.due_date ? new Date(taskToEdit.due_date).toISOString().slice(0, 16) : '');
      setPriority(taskToEdit.priority || 'medium');
      setTags(taskToEdit.tags || '');
    } else {
      setTitle('');
      setDescription('');
      setDueDate('');
      setPriority('medium');
      setTags('');
    }
  }, [taskToEdit]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!title.trim()) {
      addNotification('Title is required', 'error');
      return;
    }

    setLoading(true);

    try {
      const taskData = {
        title: title.trim(),
        description: description.trim(),
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        priority: priority,
        tags: tags.trim()
      };

      if (taskToEdit) {
        // Update existing task
        onEditComplete({ ...taskToEdit, ...taskData });
      } else {
        // Create new task
        onTaskCreated(taskData);
        setTitle('');
        setDescription('');
        setDueDate('');
        setPriority('medium');
        setTags('');
      }
    } catch (err) {
      addNotification(err.message || 'An error occurred', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    onEditComplete(null);
    setTitle('');
    setDescription('');
    setDueDate('');
    setPriority('medium');
    setTags('');
    addNotification('Edit cancelled', 'info');
  };

  return (
    <div className="task-form">
      <h2>{taskToEdit ? 'Edit Task' : 'Create New Task'}</h2>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="title">Title *</label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter task title"
            maxLength={255}
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter task description (optional)"
            maxLength={10000}
            rows={3}
            disabled={loading}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="dueDate">Due Date</label>
            <input
              id="dueDate"
              type="datetime-local"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="priority">Priority</label>
            <select
              id="priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              disabled={loading}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="tags">Tags (comma-separated)</label>
          <input
            id="tags"
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="work, personal, urgent"
            disabled={loading}
          />
        </div>

        <div className="form-actions">
          {taskToEdit && (
            <button
              type="button"
              onClick={handleCancelEdit}
              className="btn btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            className={`btn ${taskToEdit ? 'btn-primary' : 'btn-success'}`}
            disabled={loading}
          >
            {loading ? 'Saving...' : (taskToEdit ? 'Update Task' : 'Create Task')}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TaskForm;