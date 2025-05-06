import datetime
from odoo import http
from odoo.http import request
import json
import logging
import re

_logger = logging.getLogger(__name__)

def format_links(link_str, as_list=True):
    """
    Định dạng chuỗi link thành các link HTML
    Phân tách bởi dấu phẩy hoặc dấu xuống dòng (Alt+Enter trong Excel)
    """
    if not link_str:
        return ""

    # Regex để kiểm tra link có bắt đầu bằng http:// hoặc https://
    url_pattern = re.compile(r'^(http|https)://')

    # Xử lý cả dấu phẩy hoặc xuống dòng
    # Đầu tiên thay thế xuống dòng bằng dấu phẩy
    link_str = link_str.replace('\n', ',').replace('\r', ',')

    # Tách các link bởi dấu phẩy
    links = [link.strip() for link in link_str.split(',') if link.strip()]
    formatted_links = []

    for i, link in enumerate(links):
        # Kiểm tra xem chuỗi có phải là URL hợp lệ không
        if url_pattern.match(link):
            formatted_links.append(f"<a href='{link}' target='_blank'>Link {i+1}</a>")

    if not formatted_links:
        return ""

    # Định dạng danh sách nếu yêu cầu
    if as_list and len(formatted_links) > 1:
        list_items = "".join([f"<li>{link}</li>" for link in formatted_links])
        return f"<ul>{list_items}</ul>"
    else:
        # Nối các link đã định dạng bằng thẻ BR
        return "<br/>".join(formatted_links)

class WebhookController(http.Controller):
    @http.route('/webhook/google_sheet/task', type='http', auth='public', methods=['POST'], csrf=False)
    def webhook_task(self, **kw):
        _logger.info("=== WEBHOOK CALLED ===")
        try:
            # Parse JSON từ request
            data = json.loads(request.httprequest.data.decode('utf-8'))
            _logger.info("Received data: %s", data)

            # Lấy task_data là một mảng
            task_data_list = data.get('task_data', [])
            _logger.info("Task data list: %s", task_data_list)

            results = []

            # Xử lý từng task trong mảng
            for task_data in task_data_list:
                _logger.info("Processing task: %s", task_data)

                # Lấy các giá trị từ task_data
                task_code = task_data.get('task_code')
                description = task_data.get('description')
                link = task_data.get('link')

                # Định dạng link nếu có
                link_append = ""
                if link:
                    link_append = "\n\n" + format_links(link, as_list=True)

                score = task_data.get('score')
                account_id = task_data.get('account_id')
                idea = task_data.get('idea')

                #find partner_id from idea
                partner_id = request.env['res.partner'].sudo().search([('name', '=', idea)])
                if partner_id:
                    partner_id = partner_id.id
                else:
                    partner_id = None

                # format date deadline
                deadline_str = task_data.get('deadline')
                if deadline_str:
                    try:
                        deadline = datetime.datetime.strptime(deadline_str, '%d/%m/%Y %H:%M:%S')
                    except ValueError:
                        # Thử với định dạng khác nếu định dạng đầu tiên không hoạt động
                        try:
                            deadline = datetime.datetime.strptime(deadline_str, '%m/%d/%Y %H:%M:%S')
                        except ValueError:
                            _logger.warning("Không thể chuyển đổi thời gian: %s", deadline_str)
                            deadline = None
                else:
                    deadline = None
                is_urgent = task_data.get('is_urgent', False)

                # Xử lí tag_ids and seve to tag_ids in task
                if task_data.get('product'):
                    tag_names = task_data.get('product').split(',')
                    tags = request.env['project.tags'].sudo().search([('name', 'in', tag_names)])
                    if tags:
                        tag_ids = [(6, 0, tags.ids)]
                    else:
                        tag_ids = None
                else:
                    tag_ids = None

                # Sử dụng sudo() để bỏ qua kiểm tra quyền
                task = request.env['project.task'].sudo().search([('name', '=', task_code)])

                if task:
                    # cập nhật task
                    task.sudo().write({
                        'description': description + link_append,
                        'tag_ids': tag_ids,
                        'partner_id': partner_id,
                        'date_deadline': deadline,
                        'is_urgent': is_urgent,
                        'score': score,
                        'account_id' : account_id,
                    })
                    _logger.info("Task updated successfully: %s", task)
                else:
                    # tạo task mới
                    task = request.env['project.task'].sudo().create({
                        'name': task_code,
                        'description': description + link_append,
                        'project_id': 1,
                        'worksheet_template_id': 5,
                        'user_ids': [(6, 0, [1])],
                        'tag_ids': tag_ids,
                        'partner_id': partner_id,
                        'date_deadline': deadline,
                        'is_urgent': is_urgent,
                        'score': score,
                        'account_id' : account_id,
                    })
                    _logger.info("Task created successfully: %s", task)

                # Thêm kết quả vào danh sách
                results.append({
                    'task_code': task_code,
                    'status': 'success'
                })

            # Trả về kết quả
            response = {
                'success': True,
                'results': results
            }

            _logger.info("Webhook processed successfully: %s", response)
            return http.Response(
                json.dumps(response),
                status=200,
                mimetype='application/json'
            )

        except Exception as e:
            _logger.exception("Webhook error: %s", str(e))
            response = {'success': False, 'message': f"Error: {str(e)}"}
            return http.Response(
                json.dumps(response),
                status=400,
                mimetype='application/json'
            )
