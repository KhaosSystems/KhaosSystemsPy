from PySide2 import QtCore, QtWidgets, QtGui
from enum import Enum

STYLE_QMENU = '''
QMenu {
    color: rgba(255, 255, 255, 200);
    background-color: rgba(47, 47, 47, 255);
    border: 1px solid rgba(0, 0, 0, 30);
}
QMenu::item {
    padding: 5px 18px 2px;
    background-color: transparent;
}
QMenu::item:selected {
    color: rgba(98, 68, 10, 255);
    background-color: rgba(219, 158, 0, 255);
}
QMenu::separator {
    height: 1px;
    background: rgba(255, 255, 255, 50);
    margin: 4px 8px;
}
'''

class KSNodeItem(QtWidgets.QGraphicsItem):
    _contextMenu: QtWidgets.QMenu = None
    _title: str = "Node Title"

    def __init__(self):
        super().__init__()
        self.setZValue(1)

        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        self._contextMenu = QtWidgets.QMenu()
        self._contextMenu.setMinimumWidth(200)
        self._contextMenu.setStyleSheet(STYLE_QMENU)
        self._contextMenu.addAction("Remove", self.remove)

        self._brush = QtGui.QBrush()
        self._brush.setStyle(QtCore.Qt.SolidPattern)
        self._brush.setColor(QtGui.QColor(70, 70, 70, 255))

        self._pen = QtGui.QPen()
        self._pen.setStyle(QtCore.Qt.SolidLine)
        self._pen.setWidth(2)
        self._pen.setColor(QtGui.QColor(50, 50, 50, 255))

        self._penSel = QtGui.QPen()
        self._penSel.setStyle(QtCore.Qt.SolidLine)
        self._penSel.setWidth(2)
        self._penSel.setColor(QtGui.QColor(219, 158, 0, 255))

        self._textPen = QtGui.QPen()
        self._textPen.setStyle(QtCore.Qt.SolidLine)
        self._textPen.setColor(QtGui.QColor(230, 230, 230, 255))

        self._nodeTextFont = QtGui.QFont("Arial", 12, QtGui.QFont.Bold)

    @property
    def pen(self):
        if self.isSelected():
            return self._penSel
        else:
            return self._pen

    def boundingRect(self):
        return QtCore.QRectF(0, 0, 200, 25)

    def paint(self, painter, option, widget):
        # Node base.
        painter.setBrush(self._brush)
        painter.setPen(self.pen)
        painter.drawRoundedRect(0, 0, 200, 25, 10, 10)

        # Node label.
        painter.setPen(self._textPen)
        painter.setFont(self._nodeTextFont)
        metrics = QtGui.QFontMetrics(painter.font())
        text_width = metrics.boundingRect(self._title).width() + 14
        text_height = metrics.boundingRect(self._title).height() + 14
        margin = (text_width - 200) * 0.5
        textRect = QtCore.QRect(-margin, -text_height, text_width, text_height)
        painter.drawText(textRect, QtCore.Qt.AlignCenter, self._title)

    def remove(self):
        scene = self.scene()
        scene.removeItem(self)

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent) -> None:
        self._contextMenu.exec_(event.screenPos())

class KSMovementState(Enum):
    NONE = 1
    PANNING = 2
    ZOOMING = 3

class KSNodeGraph(QtWidgets.QGraphicsView):
    
    _contextMenu: QtWidgets.QMenu = None
    _lastMouseMovePosition: QtCore.QPoint = None
    _movementState: KSMovementState = KSMovementState.NONE

    # Internal variables used for camera transformation calculations.
    _lastMouseMovePosition: QtCore.QPoint = None
    _lastRightMousePressPosition:QtCore.QPoint = None
    _lastRightMousePressVerticalScalingFactor:float = None
    _lastRightMousePressHorizontalScalingFactor:float = None

    def __init__(self, parent):
        super().__init__(parent)

        self.frameSelectedAction = QtWidgets.QAction("Frame Selected", self)
        self.frameSelectedAction.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F))
        self.frameSelectedAction.triggered.connect(self.frameSelected)
        self.addAction(self.frameSelectedAction)

        self._contextMenu = QtWidgets.QMenu()
        self._contextMenu.setMinimumWidth(200)
        self._contextMenu.setStyleSheet(STYLE_QMENU)
        self._contextMenu.addAction(self.frameSelectedAction)

        self.currentState = 'DEFAULT'

        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setRenderHint(QtGui.QPainter.TextAntialiasing)
        self.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        self.setRenderHint(QtGui.QPainter.NonCosmeticDefaultPen, True)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)

        self.rubberband = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)

        scene = KSNodeScene(self)
        scene.setSceneRect(0, 0, 2000, 2000)
        self.setScene(scene)

        self.show()

    """
    def mousePressEvent(self, event):
        # Camera panning.
        if (event.button() in (QtCore.Qt.MiddleButton, QtCore.Qt.LeftButton) and event.modifiers() == QtCore.Qt.AltModifier):
            self.currentState = 'DRAG_VIEW'
            self.window().setCursor(QtCore.Qt.SizeAllCursor)
            self.setInteractive(False)

        elif (event.button() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier and self.scene().itemAt(self.mapToScene(event.pos()), QtGui.QTransform()) is None):
            self.startRubberband(event.pos())

        elif (event.button() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier and self.scene().itemAt(self.mapToScene(event.pos()), QtGui.QTransform()) is not None):
            self.currentState = 'DRAG_ITEM'
            self.setInteractive(True)
        
        else:
            self.currentState = 'DEFAULT'

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._lastMouseMovePosition == None:
            self._lastMouseMovePosition = event.pos()
            
        if self.currentState == 'DRAG_VIEW':
            delta = event.pos() - self._lastMouseMovePosition
            self.setMatrix(self.matrix().translate(delta.x(), delta.y()))

        elif (self.currentState == 'SELECTION'):
            self.updateRubberband(event.pos())

        self._lastMouseMovePosition = event.pos()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.currentState == 'SELECTION':
            self.releaseRubberband()

        self.window().setCursor(QtCore.Qt.ArrowCursor)
        self.currentState = 'DEFAULT'

        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        event.accept()
        
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        scaleFactor = (1.05) if (event.angleDelta().y() + event.angleDelta().x() > 0) else (0.95)
        self.setMatrix(self.matrix().scale(scaleFactor, scaleFactor))
   
    
    """
    # region Rubberband
    def startRubberband(self, position):
        self.currentState = 'SELECTION'
        self.rubberBandStart = position
        self.origin = position
        self.rubberband.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
        self.rubberband.show()
        self.setInteractive(False)

    def updateRubberband(self, mousePosition):
        self.rubberband.setGeometry(QtCore.QRect(self.origin, mousePosition).normalized())

    def releaseRubberband(self):
        painterPath = QtGui.QPainterPath()
        rect = self.mapToScene(self.rubberband.geometry())
        painterPath.addPolygon(rect)
        self.rubberband.hide()
        self.setInteractive(True)
        self.scene().setSelectionArea(painterPath)
    # endregion

    # region Node related
    def addNode(self, node: KSNodeItem):
        self.scene().nodes['name'] = node
        self.scene().addItem(node)
    # endregion

    def frameSelected(self):
        if len(self.scene().selectedItems()) > 0:
            selectionBounds = self.scene().selectionItemsBoundingRect()
        else:
            selectionBounds = self.scene().itemsBoundingRect()
        selectionBounds = selectionBounds.marginsAdded(QtCore.QMarginsF(64, 64+50, 64, 64))
        self.fitInView(selectionBounds, QtCore.Qt.KeepAspectRatio)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        if (self._movementState == KSMovementState.NONE and self.scene().itemAt(self.mapToScene(event.pos()), QtGui.QTransform()) is None):
            self._contextMenu.exec_(event.globalPos())
        else:
            super().contextMenuEvent(event)

    # region Mouse events
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        super().keyPressEvent(event)

        # Frame selected.
        if event.key() == QtCore.Qt.Key_F:
            self.frameSelected()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(event)

        if event.button() == QtCore.Qt.RightButton:
            self._lastRightMousePressPosition = event.pos()
            self._lastRightMousePressHorizontalScalingFactor = self.matrix().m11()
            self._lastRightMousePressVerticalScalingFactor = self.matrix().m22()

        # Camera panning
        if (QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier and event.button() in (QtCore.Qt.MiddleButton, QtCore.Qt.LeftButton)):
            self.window().setCursor(QtCore.Qt.SizeAllCursor)
            self._movementState = KSMovementState.PANNING

        # Camera mouse zoom
        elif (QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier and event.button() == QtCore.Qt.RightButton):
            self.window().setCursor(QtCore.Qt.SizeVerCursor)
            self._movementState = KSMovementState.ZOOMING

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        
        if (self._movementState != KSMovementState.NONE):
            self._movementState = KSMovementState.NONE
            self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.PreventContextMenu)
            self.window().setCursor(QtCore.Qt.ArrowCursor)
        else:
            self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.DefaultContextMenu)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(event)

        # If these positions are not set/set to null vector, the later code will cause wired behaviour.
        if self._lastMouseMovePosition == None:
            self._lastMouseMovePosition = event.pos()
        if self._lastRightMousePressPosition == None:
            self._lastRightMousePressPosition = event.pos()

        # Camera panning
        if self._movementState == KSMovementState.PANNING:
            delta = event.pos() - self._lastMouseMovePosition
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

        # Camera mouse zoom.
        if self._movementState == KSMovementState.ZOOMING:
            """ 
            Camera zooming; this is some freaking messy math, don't judge; it works pretty well! xD
            There is most likely a cleaner way of doing this but i honestly can't bother finding it.
            If this is triggering to you, feel free to hit me with a pull request.
            """
            self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
            # TODO: Make zooming slower when distanceToOrigin increases
            # Capture data for correcting view translation offset.
            oldSceneSpaceOriginPoint = self.mapToScene(self._lastRightMousePressPosition)
            ### Calculate scaleing factor
            cursorPoint = QtGui.QVector2D(event.pos())
            originPoint = QtGui.QVector2D(self._lastRightMousePressPosition)
            orientationPoint = originPoint + QtGui.QVector2D(1, 1)
            orientationVector = orientationPoint - originPoint
            cursorVector = orientationPoint - cursorPoint
            # Introduce a small constant value if the vector length is 0.
            # This is needed since the vector normalization calulation will cause an error if the vector has a length of 0
            orientationVector = (orientationVector + QtGui.QVector2D(0.001, 0.001)) if bool(orientationVector.length() == 0) else orientationVector
            cursorVector = (cursorVector + QtGui.QVector2D(0.001, 0.001)) if bool(cursorVector.length() == 0) else cursorVector
            orientationUnitVector = orientationVector.normalized() # Normalization calulation
            cursorUnitVector = cursorVector.normalized() # Normalization calulation
            dotProduct = QtGui.QVector2D.dotProduct(orientationUnitVector, cursorUnitVector)
            distanceToOrigin = originPoint.distanceToPoint(cursorPoint)
            globalScaleFactor = 1 - (dotProduct * distanceToOrigin * 0.0015) # dot * dist * zoomSensitivity
            ### Create the actial matrix for applying the scale; the initial scaleing factors should be set on mouse putton pressed.
            finalHorizontalScalingFactor = min(max(self._lastRightMousePressHorizontalScalingFactor * globalScaleFactor, 0.2), 2)
            finalVerticalScalingFactor = min(max(self._lastRightMousePressVerticalScalingFactor * globalScaleFactor, 0.2), 2)
            # print(finalHorizontalScalingFactor)
            # print(finalVerticalScalingFactor) 
            horizontalScalingFactor = finalHorizontalScalingFactor # FIXME: This should possibly not by multiplying since it wont be linear; i think...
            verticalScalingFactor = finalVerticalScalingFactor # FIXME: If addition or subtraction is the correct way to go, the globalScaleFactor range need to change.
            verticalShearingFactor = self.matrix().m12()
            horizontalShearingFactor = self.matrix().m21()
            self.setMatrix(QtGui.QMatrix(horizontalScalingFactor, verticalShearingFactor, horizontalShearingFactor, verticalScalingFactor, self.matrix().dx(), self.matrix().dy()))
            # Correct view translation offset.
            newSceneSpaceOriginPoint = self.mapToScene(self._lastRightMousePressPosition)
            translationDelta = newSceneSpaceOriginPoint - oldSceneSpaceOriginPoint;
            self.translate(translationDelta.x(), translationDelta.y())
       
        # Capture necessary data used for camera transformation. 
        self._lastMouseMovePosition = event.pos()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        event.accept()
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        scaleFactor = (1.05) if (event.angleDelta().y() + event.angleDelta().x() > 0) else (0.95)
        self.scale(scaleFactor, scaleFactor)
    # endregion
class KSNodeScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.setBackgroundBrush(QtGui.QColor(26, 26, 26))
        self.nodes = dict()

    def addItem(self, item: QtWidgets.QGraphicsItem) -> None:
        super().addItem(item)
        self.setSceneRect(self.itemsBoundingRect().marginsAdded(QtCore.QMarginsF(1024*128, 1024*128, 1024*128, 1024*128)))

    def selectionItemsBoundingRect(self) -> QtCore.QRectF:
        # Does not take untransformable items into account.
        boundingRect = QtCore.QRectF()
        for item in self.selectedItems():
            boundingRect |= item.sceneBoundingRect()
        return boundingRect