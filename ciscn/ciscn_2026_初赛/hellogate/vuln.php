<?php
error_reporting(0);        // 题目里用的
class A {
    public $handle;
    public function triggerMethod() {
        echo "" . $this->handle;
    }
}
class B {
    public $worker;
    public $cmd;
    public function __toString() {
        // PHP 7+ 必须返回字符串
        return $this->worker->result ?? '';
    }
}
class C {
    public $cmd;
    public function __get($name) {
        echo file_get_contents($this->cmd);
    }
}

// 读取 flag.txt（你可以改成任何你想读的文件）
// 这里直接演示，把 POST 的 data 直接反序列化
$raw = isset($_POST['data']) ? $_POST['data'] : '';
// 下面这两行是题目原来给的，跑本地时可注释
// header('Content-Type: image/jpeg');
// readfile("muzujijiji.jpg");

//highlight_file(__FILE__);   // 注释掉

$obj = unserialize($_POST['data'] ?? '');
if ($obj) $obj->triggerMethod();
?>
